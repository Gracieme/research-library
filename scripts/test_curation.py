import unittest

from curation import inspiration_rejection_reason, is_inspiring_paper


class CurationTests(unittest.TestCase):
    def test_accepts_mainline_paper_with_transfer_move(self):
        paper = {
            "title": "Teacher vulnerability and institutional discourse",
            "abstract": "A critical discourse study of emotional labor in dual language immersion.",
            "relevance": "主线：推进教师结构性脆弱研究。启发点：改变分析单位。可迁移动作：比较政策承诺与投诉处理。",
        }
        self.assertTrue(is_inspiring_paper(paper))

    def test_rejects_retired_micm_line(self):
        paper = {
            "title": "Language-related episodes in CSL peer interaction",
            "abstract": "Negotiation of meaning and LRE onset.",
            "relevance": "可迁移动作：重做MICM编码。",
        }
        self.assertIn("retired", inspiration_rejection_reason(paper))

    def test_rejects_explicitly_peripheral_paper(self):
        paper = {
            "title": "General social media research",
            "abstract": "A broad review of social media.",
            "relevance": "这篇与研究仅有微弱关联。可迁移动作：无。",
        }
        self.assertIn("weak or peripheral", inspiration_rejection_reason(paper))

    def test_rejects_future_ingest_without_transfer_move(self):
        paper = {
            "title": "Language assessment fairness",
            "abstract": "A strong study of multilingual assessment and justice.",
            "relevance": "这篇与跨国评估公平高度相关。",
        }
        self.assertIn("transferable", inspiration_rejection_reason(paper, True))
        self.assertEqual(inspiration_rejection_reason(paper, False), "")


if __name__ == "__main__":
    unittest.main()
