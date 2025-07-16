"""
Data models for taxonomy structures.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from openai.types import CompletionUsage


@dataclass
class Subtopic:
    """Represents a subtopic within a main topic."""
    subtopic_name: str
    subtopic_short_description: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {
            "subtopicName": self.subtopic_name,
            "subtopicShortDescription": self.subtopic_short_description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Subtopic':
        """Create from dictionary."""
        return cls(
            subtopic_name=data["subtopicName"],
            subtopic_short_description=data["subtopicShortDescription"]
        )


@dataclass
class Topic:
    """Represents a main topic with subtopics."""
    topic_name: str
    topic_short_description: str
    subtopics: List[Subtopic]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "topicName": self.topic_name,
            "topicShortDescription": self.topic_short_description,
            "subtopics": [subtopic.to_dict() for subtopic in self.subtopics]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Topic':
        """Create from dictionary."""
        return cls(
            topic_name=data["topicName"],
            topic_short_description=data["topicShortDescription"],
            subtopics=[Subtopic.from_dict(st) for st in data["subtopics"]]
        )


@dataclass
class Taxonomy:
    """Represents the complete taxonomy structure."""
    taxonomy: List[Topic]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "taxonomy": [topic.to_dict() for topic in self.taxonomy]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Taxonomy':
        """Create from dictionary."""
        return cls(
            taxonomy=[Topic.from_dict(topic) for topic in data["taxonomy"]]
        )
    
    def get_topic_tree(self) -> List[Dict[str, Any]]:
        """Get core tree structure for display."""
        core_tree = []
        for topic in self.taxonomy:
            subtopic_list = []
            for subtopic in topic.subtopics:
                subtopic_list.append({subtopic.subtopic_name: subtopic.subtopic_short_description})
            core_tree.append({
                topic.topic_name: topic.topic_short_description,
                "subtopic": subtopic_list
            })
        return core_tree
    
    def get_num_themes(self) -> int:
        """Get number of themes."""
        return len(self.taxonomy)
    
    def get_num_topics(self) -> int:
        """Get total number of subtopics."""
        return sum(len(topic.subtopics) for topic in self.taxonomy)
    
    def get_subtopics_counts(self) -> List[int]:
        """Get list of subtopic counts per theme."""
        return [len(topic.subtopics) for topic in self.taxonomy]


@dataclass
class TaxonomyResponse:
    """Response from the taxonomy creation step."""
    taxonomy: Taxonomy
    usage: CompletionUsage
    
    @classmethod
    def from_llm_response(cls, response_dict: Dict[str, Any], usage: CompletionUsage) -> 'TaxonomyResponse':
        """Create from LLM response."""
        return cls(
            taxonomy=Taxonomy.from_dict(response_dict),
            usage=usage
        ) 