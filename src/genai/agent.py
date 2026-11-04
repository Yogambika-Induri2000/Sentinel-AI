import sys
import os
import warnings
warnings.filterwarnings("ignore")

import psycopg2
from sentence_transformers import SentenceTransformer
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

# Ensure project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from config.setting import settings

# Load local embedding model for vector search queries
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


# ---------------------------------------------------------
# Core Search Logic Functions (Direct Python Functions)
# ---------------------------------------------------------
def search_vectors_direct(query_text: str) -> str:
    """Core PostgreSQL pgvector cosine similarity search."""
    try:
        query_vector = embedding_model.encode(query_text).tolist()
        
        conn = psycopg2.connect(settings.postgres_uri)
        cur = conn.cursor()
        
        sql = """
            SELECT v.video_id, v.claim_status, ve.transcription_chunk,
                   (ve.embedding <=> %s::vector) AS distance
            FROM video_embeddings ve
            JOIN videos v ON ve.video_id = v.video_id
            ORDER BY distance ASC
            LIMIT 5;
        """
        cur.execute(sql, (query_vector,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return "No semantically similar transcriptions found in pgvector."

        results = []
        for r in rows:
            results.append(
                f"Video ID: {r[0]} | Claim Status: {r[1]} | Cosine Distance: {r[3]:.4f}\n"
                f"Transcript: {r[2]}"
            )
        return "\n\n".join(results)
    except Exception as e:
        return f"Vector Search Database Error: {str(e)}"


def execute_sql_direct(query_sql: str) -> str:
    """Core PostgreSQL relational SQL query executor."""
    try:
        conn = psycopg2.connect(settings.postgres_uri)
        cur = conn.cursor()
        cur.execute(query_sql)
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        
        if not rows:
            return "No records found matching the SQL query."
        
        result = [dict(zip(colnames, row)) for row in rows[:10]]
        return str(result)
    except Exception as e:
        return f"SQL Execution Error: {str(e)}"


# ---------------------------------------------------------
# LangChain Tool Wrappers for Agentic Router
# ---------------------------------------------------------
@tool
def run_sql_query(query: str) -> str:
    """Executes a SQL SELECT query against the PostgreSQL analytical database table 'videos'."""
    return execute_sql_direct(query)


@tool
def run_vector_search(query: str) -> str:
    """Performs semantic vector similarity search on TikTok video transcriptions."""
    return search_vectors_direct(query)


# ---------------------------------------------------------
# Sentinel-AI Agent Builder
# ---------------------------------------------------------
def build_sentinel_agent(openai_api_key: str):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_api_key)

    tools = [run_sql_query, run_vector_search]

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are Sentinel-AI, an expert Data Engineering and Misinformation Threat Intelligence Assistant.
        You have access to a live PostgreSQL analytical store and a pgvector similarity search database of TikTok video data.
        
        Determine whether the user's request requires analytical metrics (Text-to-SQL), semantic transcript lookup (Vector Search), or both.
        Synthesize tool outputs clearly and concisely."""),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)


if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️ OPENAI_API_KEY environment variable not set. Running direct vector search test...\n")
        print(search_vectors_direct("drone deliveries and soil microorganisms"))
    else:
        agent_executor = build_sentinel_agent(api_key)
        print("🤖 Sentinel-AI Agent ready! Running test query...\n")
        response = agent_executor.invoke({"input": "What is the total view count of unverified accounts with claim status 'claim'?"})
        print("\nAgent Answer:\n", response["output"])