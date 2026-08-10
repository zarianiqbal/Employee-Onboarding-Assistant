#!/usr/bin/env python3
"""Ingest company policy documents into Azure AI Search.

Reads the markdown policy corpus, chunks it by section, embeds each chunk with
an Azure OpenAI embedding deployment, and uploads the vectors + text into an
Azure AI Search index for the RAG pipeline. It only ever reads from the
`company-policies` container / local corpus — never employee PII.

Authentication is secretless (DefaultAzureCredential). Run locally with
`az login`, or in CI with a federated identity.

Usage:
    python scripts/ingest_policies.py --recreate-index
"""
from __future__ import annotations

import argparse
import logging

from app.core.config import get_settings
from app.services.knowledge_base import load_chunks

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("ingest")

INDEX_FIELDS = ["id", "title", "heading", "source", "content", "content_vector"]


def build_index(recreate: bool) -> None:
    from azure.identity import DefaultAzureCredential
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        HnswAlgorithmConfiguration,
        SearchableField,
        SearchField,
        SearchFieldDataType,
        SearchIndex,
        SimpleField,
        VectorSearch,
        VectorSearchProfile,
    )

    settings = get_settings()
    client = SearchIndexClient(settings.azure_search_endpoint, DefaultAzureCredential())

    if recreate:
        try:
            client.delete_index(settings.azure_search_index)
            logger.info("Deleted existing index %s", settings.azure_search_index)
        except Exception:  # noqa: BLE001 - index may not exist yet
            logger.info("No existing index to delete")

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="heading", type=SearchFieldDataType.String),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=3072,  # text-embedding-3-large
            vector_search_profile_name="default",
        ),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="default", algorithm_configuration_name="hnsw")],
    )
    index = SearchIndex(
        name=settings.azure_search_index, fields=fields, vector_search=vector_search
    )
    client.create_or_update_index(index)
    logger.info("Ensured index %s exists", settings.azure_search_index)


def embed(texts: list[str]) -> list[list[float]]:
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from openai import AzureOpenAI

    settings = get_settings()
    client = AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        azure_ad_token_provider=get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        ),
    )
    resp = client.embeddings.create(
        model=settings.azure_openai_embedding_deployment, input=texts
    )
    return [item.embedding for item in resp.data]


def upload_chunks() -> None:
    from azure.identity import DefaultAzureCredential
    from azure.search.documents import SearchClient

    settings = get_settings()
    chunks = load_chunks()
    if not chunks:
        logger.warning("No policy chunks found — nothing to ingest")
        return

    vectors = embed([c.text for c in chunks])
    documents = [
        {
            "id": str(i),
            "title": c.doc_title,
            "heading": c.heading,
            "source": c.source,
            "content": c.text,
            "content_vector": vec,
        }
        for i, (c, vec) in enumerate(zip(chunks, vectors, strict=True))
    ]

    client = SearchClient(
        settings.azure_search_endpoint,
        settings.azure_search_index,
        DefaultAzureCredential(),
    )
    client.upload_documents(documents)
    logger.info("Uploaded %d chunks to %s", len(documents), settings.azure_search_index)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest policy docs into Azure AI Search.")
    parser.add_argument("--recreate-index", action="store_true", help="drop + recreate the index")
    args = parser.parse_args()

    settings = get_settings()
    if not (settings.search_configured and settings.openai_configured):
        raise SystemExit(
            "AZURE_SEARCH_ENDPOINT and AZURE_OPENAI_ENDPOINT must be set to ingest."
        )

    build_index(args.recreate_index)
    upload_chunks()


if __name__ == "__main__":
    main()
