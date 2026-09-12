from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


print("Loading semantic model...")

model = SentenceTransformer("all-MiniLM-L6-v2")


def semantic_score(jd_text, resume_text):
    """
    Calculate semantic similarity between the job description
    and a candidate's relevant resume content.

    Returns a score between 0 and 1.
    """

    jd_embedding = model.encode([jd_text])
    resume_embedding = model.encode([resume_text])

    score = cosine_similarity(
        jd_embedding,
        resume_embedding
    )[0][0]

    return float(score)


if __name__ == "__main__":

    jd_text = """
    Looking for a Python developer with experience in
    machine learning, REST APIs, SQL and backend development.
    """

    resume_text = """
    Developed backend applications using Python and REST APIs.
    Worked on machine learning projects and database systems
    using SQL.
    """

    score = semantic_score(jd_text, resume_text)

    print("Semantic score:", score)