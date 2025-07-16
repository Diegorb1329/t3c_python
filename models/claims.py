"""
Data models for claims structures.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from openai.types import CompletionUsage


@dataclass
class Claim:
    """Represents a single claim extracted from a comment."""
    claim: str
    quote: str
    topic_name: str
    subtopic_name: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {
            "claim": self.claim,
            "quote": self.quote,
            "topicName": self.topic_name,
            "subtopicName": self.subtopic_name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Claim':
        """Create from dictionary."""
        return cls(
            claim=data["claim"],
            quote=data["quote"],
            topic_name=data["topicName"],
            subtopic_name=data["subtopicName"]
        )


@dataclass
class ClaimsExtraction:
    """Represents claims extracted from a single comment."""
    claims: List[Claim]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "claims": [claim.to_dict() for claim in self.claims]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClaimsExtraction':
        """Create from dictionary."""
        return cls(
            claims=[Claim.from_dict(claim) for claim in data.get("claims", [])]
        )
    
    def get_num_claims(self) -> int:
        """Get number of claims."""
        return len(self.claims)


@dataclass
class ClaimsResponse:
    """Response from the claims extraction step."""
    claims_extraction: ClaimsExtraction
    usage: CompletionUsage
    
    @classmethod
    def from_llm_response(cls, response_dict: Dict[str, Any], usage: CompletionUsage) -> 'ClaimsResponse':
        """Create from LLM response."""
        return cls(
            claims_extraction=ClaimsExtraction.from_dict(response_dict),
            usage=usage
        )


@dataclass
class SubtopicClaims:
    """Represents claims grouped by subtopic."""
    subtopic_name: str
    claims: List[str]
    total_count: int
    
    def __init__(self, subtopic_name: str, claims: List[str]):
        self.subtopic_name = subtopic_name
        self.claims = claims
        self.total_count = len(claims)


@dataclass
class TopicClaims:
    """Represents claims grouped by topic."""
    topic_name: str
    subtopics: Dict[str, SubtopicClaims]
    total_count: int
    
    def __init__(self, topic_name: str, subtopics: Dict[str, SubtopicClaims]):
        self.topic_name = topic_name
        self.subtopics = subtopics
        self.total_count = sum(subtopic.total_count for subtopic in subtopics.values())


@dataclass
class SortedTaxonomy:
    """Represents taxonomy sorted by claim frequency."""
    topics: Dict[str, TopicClaims]
    
    def get_total_topics(self) -> int:
        """Get total number of topics."""
        return sum(len(topic.subtopics) for topic in self.topics.values())
    
    def get_total_claims(self) -> int:
        """Get total number of claims."""
        return sum(topic.total_count for topic in self.topics.values())


@dataclass
class DuplicateGroup:
    """Represents a group of duplicate claims."""
    main_claim_id: str
    duplicate_ids: List[str]
    
    def to_dict(self) -> Dict[str, List[str]]:
        """Convert to dictionary format."""
        return {self.main_claim_id: self.duplicate_ids}


@dataclass
class DeduplicationResult:
    """Represents the result of deduplication."""
    nesting: Dict[str, List[str]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {"nesting": self.nesting}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeduplicationResult':
        """Create from dictionary."""
        return cls(nesting=data.get("nesting", {}))
    
    def has_duplicates(self) -> bool:
        """Check if there are any duplicates."""
        return any(len(duplicates) > 0 for duplicates in self.nesting.values())


@dataclass
class DeduplicationResponse:
    """Response from the deduplication step."""
    deduplication_result: DeduplicationResult
    usage: CompletionUsage
    
    @classmethod
    def from_llm_response(cls, response_dict: Dict[str, Any], usage: CompletionUsage) -> 'DeduplicationResponse':
        """Create from LLM response."""
        return cls(
            deduplication_result=DeduplicationResult.from_dict(response_dict),
            usage=usage
        ) 