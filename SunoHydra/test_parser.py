import unittest
from parser import SunoTrack, CleanedTrack

class TestSunoParser(unittest.TestCase):
    def test_high_status_filter(self):
        # High status track
        t1 = CleanedTrack(
            track_id="123",
            title="Hit",
            play_count=1500,
            upvote_count=100,
            raw_tags=["pop"],
            model_version="v3"
        )
        self.assertTrue(t1.is_high_status)

        # Low status track
        t2 = CleanedTrack(
            track_id="456",
            title="Flop",
            play_count=50,
            upvote_count=2,
            raw_tags=["noise"],
            model_version="v3"
        )
        self.assertFalse(t2.is_high_status)

    def test_pydantic_parsing(self):
        raw_data = {
            "id": "abc-123",
            "title": "Cool Song",
            "metadata": {
                "tags": "rock, metal"
            },
            "play_count": 5000,
            "major_model_version": "v3"
        }
        
        track = SunoTrack(**raw_data)
        self.assertEqual(track.play_count, 5000)
        
        # Test tag extraction logic simulation
        extracted_tags = [t.strip() for t in track.metadata["tags"].split(",")]
        cleaned = CleanedTrack(
            track_id=track.id,
            title=track.title,
            play_count=track.play_count,
            upvote_count=track.upvote_count,
            raw_tags=extracted_tags,
            model_version=track.major_model_version
        )
        
        self.assertEqual(cleaned.raw_tags, ["rock", "metal"])
        self.assertTrue(cleaned.is_high_status)

if __name__ == '__main__':
    unittest.main()
