"""Skills taxonomy used by the skill-extraction NER component.

Kept as a plain Python dict (not a DB/service) on purpose: it's small, it's
versioned in git like everything else, and it's trivial to extend by editing
one file. Categories are used for grouping in the dashboard's gap analysis.
"""

SKILLS_TAXONOMY = {
    "Programming Languages": [
        "Python", "Java", "C++", "C", "JavaScript", "TypeScript", "Go", "Rust",
        "SQL", "R", "Scala", "Kotlin", "Swift", "PHP", "Ruby", "MATLAB",
    ],
    "Web & Frameworks": [
        "React", "Angular", "Vue.js", "Node.js", "Django", "Flask", "FastAPI",
        "Spring Boot", "Express.js", "HTML", "CSS", "REST API", "GraphQL",
    ],
    "Data & ML": [
        "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
        "TensorFlow", "PyTorch", "scikit-learn", "Keras", "Pandas", "NumPy",
        "Data Analysis", "Data Visualization", "Statistics", "XGBoost",
        "Feature Engineering", "MLOps",
    ],
    "Big Data & Cloud": [
        "Apache Spark", "Hadoop", "Kafka", "Airflow", "Hive", "AWS", "Azure",
        "GCP", "Docker", "Kubernetes", "Elasticsearch", "Delta Lake",
        "Data Warehousing", "ETL", "Snowflake",
    ],
    "Databases": [
        "MySQL", "PostgreSQL", "MongoDB", "Redis", "Cassandra", "Oracle",
        "SQLite", "DynamoDB",
    ],
    "Tools & Practices": [
        "Git", "Linux", "CI/CD", "Jenkins", "Agile", "Scrum", "JIRA",
        "Unit Testing", "System Design", "Microservices",
    ],
    "Soft Skills": [
        "Communication", "Teamwork", "Leadership", "Problem Solving",
        "Time Management", "Critical Thinking",
    ],
    "Certifications": [
        "AWS Certified Solutions Architect", "Google Data Analytics",
        "PMP", "CCNA", "Salesforce Certified", "Azure Fundamentals",
    ],
}


def flat_skill_list() -> list[str]:
    """All skills across categories, as a flat list (for building the matcher)."""
    return [skill for skills in SKILLS_TAXONOMY.values() for skill in skills]


def skill_to_category() -> dict[str, str]:
    return {
        skill: category
        for category, skills in SKILLS_TAXONOMY.items()
        for skill in skills
    }
