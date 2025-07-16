"""
Data loading utilities for the T3C pipeline.
"""

import pandas as pd
from typing import List, Optional
import os


class DataLoader:
    """Utility for loading comments from various sources."""
    
    @staticmethod
    def load_from_csv(csv_path: str, comment_column: str = "comment") -> List[str]:
        """Load comments from a CSV file."""
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            if comment_column not in df.columns:
                raise ValueError(f"Column '{comment_column}' not found in CSV. Available columns: {list(df.columns)}")
            
            comments = df[comment_column].tolist()
            
            # Filter out non-string values
            comments = [str(c) for c in comments if pd.notna(c) and str(c).strip()]
            
            return comments
            
        except Exception as e:
            raise RuntimeError(f"Error loading CSV file: {str(e)}")
    
    @staticmethod
    def load_from_list(comments: List[str]) -> List[str]:
        """Load comments from a Python list."""
        if not isinstance(comments, list):
            raise TypeError("Comments must be a list")
        
        # Filter out non-string values and empty strings
        filtered_comments = []
        for comment in comments:
            if isinstance(comment, str) and comment.strip():
                filtered_comments.append(comment)
            elif comment is not None:
                # Convert to string if not None
                str_comment = str(comment).strip()
                if str_comment:
                    filtered_comments.append(str_comment)
        
        return filtered_comments
    
    @staticmethod
    def get_test_data(test_type: str = "scifi") -> List[str]:
        """Get test data for development and testing."""
        if test_type == "pets":
            return DataLoader._get_pets_test_data()
        elif test_type == "scifi":
            return DataLoader._get_scifi_test_data()
        else:
            raise ValueError(f"Unknown test type: {test_type}. Available: 'pets', 'scifi'")
    
    @staticmethod
    def _get_pets_test_data() -> List[str]:
        """Get pets test data from the notebook."""
        pets_data = [
            "I love cats", "I really really love dogs", "I'm not sure about birds",
            "Cats are my favorite", "Dogs are the best", "No seriously dogs are great",
            "Birds I'm hesitant about", "Cats can be walked outside and they don't have to",
            "Dogs need to be walked regularly, every day",
            "Dogs can be trained to perform adorable moves on verbal command",
            "Can cats be trained?", "Dogs and cats are both adorable and fluffy",
            "Good pets are chill", "Cats are fantastic", "A goldfish is my top choice",
            "Lizards are scary", "Kittens are my favorite when they have snake-like scales",
            "Hairless cats are unique", "Flying lizards are majestic", "Kittens are so boring"
        ]
        return pets_data
    
    @staticmethod
    def _get_scifi_test_data() -> List[str]:
        """Get sci-fi test data from the notebook."""
        scifi_data = [
            "My favorite fantasy novel is Name of the Wind",
            "Terra Ignota is the best scifi series of all time",
            "Idk about Kim Stanley Robinson",
            "Name of the Wind is predictable and hard to read",
            "Some of Kim Stanley Robinson is boring",
            "Terra Ignota gets slow in the middle and hard to follow",
            "Ada Palmer is spectacular",
            "Becky Chambers has fantastic aliens in her work",
            "Ministry for the Future and Years of Rice and Salt are really comprehensive and compelling stories",
            "Do we still talk about Lord of the Rings or Game of Thrones or is epic fantasy over",
            "What about Ted Chiang he is so good",
            "Greg Egan is really good at characters and plot and hard science",
            "I never finished Accelerando",
            "Ministry for the Future is about the climate transition",
            "The climate crisis is a major theme in Ministry for the Future",
            "Ministry for the Future is about climate"
        ]
        return scifi_data
    
    @staticmethod
    def validate_comments(comments: List[str]) -> tuple:
        """Validate and clean comments list."""
        if not comments:
            raise ValueError("Comments list is empty")
        
        original_count = len(comments)
        
        # Clean and validate
        cleaned_comments = []
        for i, comment in enumerate(comments):
            if not isinstance(comment, str):
                continue
            
            comment = comment.strip()
            if not comment:
                continue
            
            cleaned_comments.append(comment)
        
        final_count = len(cleaned_comments)
        
        if final_count == 0:
            raise ValueError("No valid comments found after cleaning")
        
        return cleaned_comments, original_count, final_count
    
    @staticmethod
    def get_comment_stats(comments: List[str]) -> dict:
        """Get statistics about the comments."""
        if not comments:
            return {"count": 0, "total_chars": 0, "avg_length": 0, "lengths": []}
        
        lengths = [len(c) for c in comments]
        total_chars = sum(lengths)
        
        return {
            "count": len(comments),
            "total_chars": total_chars,
            "avg_length": total_chars / len(comments) if comments else 0,
            "min_length": min(lengths) if lengths else 0,
            "max_length": max(lengths) if lengths else 0,
            "lengths": lengths
        } 