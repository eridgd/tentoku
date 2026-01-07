"""
Comprehensive tests for deinflection.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tentoku.deinflect import deinflect
from tentoku._types import WordType, Reason


class TestDeinflect(unittest.TestCase):
    """Test deinflection functions."""
    
    def test_deinflect_ichidan_verb_te_form(self):
        """Test deinflection of ichidan verb te-form."""
        candidates = deinflect("食べて")
        self.assertGreater(len(candidates), 0)
        found_taberu = any(c.word == "食べる" for c in candidates)
        self.assertTrue(found_taberu)
    
    def test_deinflect_ichidan_verb_past(self):
        """Test deinflection of ichidan verb past form."""
        candidates = deinflect("食べた")
        found_taberu = any(c.word == "食べる" for c in candidates)
        self.assertTrue(found_taberu)
    
    def test_deinflect_ichidan_verb_negative(self):
        """Test deinflection of ichidan verb negative form."""
        candidates = deinflect("食べない")
        found_taberu = any(c.word == "食べる" for c in candidates)
        self.assertTrue(found_taberu)
    
    def test_deinflect_godan_verb_te_form(self):
        """Test deinflection of godan verb te-form."""
        candidates = deinflect("読んで")
        found_yomu = any(c.word == "読む" for c in candidates)
        self.assertTrue(found_yomu)
    
    def test_deinflect_godan_verb_past(self):
        """Test deinflection of godan verb past form."""
        candidates = deinflect("読んだ")
        found_yomu = any(c.word == "読む" for c in candidates)
        self.assertTrue(found_yomu)
    
    def test_deinflect_godan_verb_negative(self):
        """Test deinflection of godan verb negative form."""
        candidates = deinflect("読まない")
        found_yomu = any(c.word == "読む" for c in candidates)
        self.assertTrue(found_yomu)
    
    def test_deinflect_i_adj_ku_form(self):
        """Test deinflection of i-adjective ku-form."""
        candidates = deinflect("高く")
        found_takai = any(c.word == "高い" for c in candidates)
        self.assertTrue(found_takai)
    
    def test_deinflect_i_adj_past(self):
        """Test deinflection of i-adjective past form."""
        candidates = deinflect("高かった")
        found_takai = any(c.word == "高い" for c in candidates)
        self.assertTrue(found_takai)
    
    def test_deinflect_i_adj_negative(self):
        """Test deinflection of i-adjective negative form."""
        candidates = deinflect("高くない")
        found_takai = any(c.word == "高い" for c in candidates)
        self.assertTrue(found_takai)
    
    def test_deinflect_suru_verb(self):
        """Test deinflection of suru verb."""
        candidates = deinflect("して")
        found_suru = any(c.word == "する" for c in candidates)
        self.assertTrue(found_suru)
        
        candidates = deinflect("した")
        found_suru = any(c.word == "する" for c in candidates)
        self.assertTrue(found_suru)
        
        candidates = deinflect("しない")
        found_suru = any(c.word == "する" for c in candidates)
        self.assertTrue(found_suru)
    
    def test_deinflect_kuru_verb(self):
        """Test deinflection of kuru verb."""
        candidates = deinflect("来て")
        found_kuru = any(c.word == "来る" or c.word == "くる" for c in candidates)
        self.assertTrue(found_kuru)
        
        candidates = deinflect("来た")
        found_kuru = any(c.word == "来る" or c.word == "くる" for c in candidates)
        self.assertTrue(found_kuru)
    
    def test_deinflect_multiple_steps(self):
        """Test deinflection with multiple steps."""
        # 食べていません → 食べる
        candidates = deinflect("食べていません")
        found_taberu = any(c.word == "食べる" for c in candidates)
        self.assertTrue(found_taberu)
    
    def test_deinflect_already_plain_form(self):
        """Test deinflection of already plain form."""
        candidates = deinflect("食べる")
        # Should include the original word
        found_taberu = any(c.word == "食べる" for c in candidates)
        self.assertTrue(found_taberu)
    
    def test_deinflect_reason_chains(self):
        """Test that reason chains are tracked."""
        candidates = deinflect("食べて")
        taberu_candidate = next((c for c in candidates if c.word == "食べる"), None)
        if taberu_candidate:
            self.assertIsNotNone(taberu_candidate.reason_chains)
            self.assertGreater(len(taberu_candidate.reason_chains), 0)
    
    def test_deinflect_polite_past(self):
        """Test deinflection of polite past form (ました)."""
        candidates = deinflect("食べました")
        taberu_candidate = next((c for c in candidates if c.word == "食べる"), None)
        self.assertIsNotNone(taberu_candidate, "Should deinflect 食べました to 食べる")
        if taberu_candidate:
            # Should have PolitePast reason
            has_polite_past = any(
                Reason.PolitePast in chain
                for chain in taberu_candidate.reason_chains
            )
            self.assertTrue(has_polite_past, "Should identify as PolitePast")
    
    def test_deinflect_continuous(self):
        """Test deinflection of continuous form (ている)."""
        candidates = deinflect("食べている")
        taberu_candidate = next((c for c in candidates if c.word == "食べる"), None)
        self.assertIsNotNone(taberu_candidate, "Should deinflect 食べている to 食べる")
        if taberu_candidate:
            # Should have Continuous reason
            has_continuous = any(
                Reason.Continuous in chain
                for chain in taberu_candidate.reason_chains
            )
            self.assertTrue(has_continuous, "Should identify as Continuous")
    
    def test_deinflect_negative(self):
        """Test deinflection of negative form (ない)."""
        candidates = deinflect("食べない")
        taberu_candidate = next((c for c in candidates if c.word == "食べる"), None)
        self.assertIsNotNone(taberu_candidate, "Should deinflect 食べない to 食べる")
        if taberu_candidate:
            # Should have Negative reason
            has_negative = any(
                Reason.Negative in chain
                for chain in taberu_candidate.reason_chains
            )
            self.assertTrue(has_negative, "Should identify as Negative")
    
    def test_deinflect_polite(self):
        """Test deinflection of polite form (ます)."""
        candidates = deinflect("食べます")
        taberu_candidate = next((c for c in candidates if c.word == "食べる"), None)
        self.assertIsNotNone(taberu_candidate, "Should deinflect 食べます to 食べる")
        if taberu_candidate:
            # Should have Polite reason
            has_polite = any(
                Reason.Polite in chain
                for chain in taberu_candidate.reason_chains
            )
            self.assertTrue(has_polite, "Should identify as Polite")
    
    def test_deinflect_tai_form(self):
        """Test deinflection of tai form (たい)."""
        candidates = deinflect("食べたい")
        taberu_candidate = next((c for c in candidates if c.word == "食べる"), None)
        self.assertIsNotNone(taberu_candidate, "Should deinflect 食べたい to 食べる")
        if taberu_candidate:
            # Should have Tai reason
            has_tai = any(
                Reason.Tai in chain
                for chain in taberu_candidate.reason_chains
            )
            self.assertTrue(has_tai, "Should identify as Tai form")
    
    def test_deinflect_past(self):
        """Test deinflection of past form (た)."""
        candidates = deinflect("食べた")
        taberu_candidate = next((c for c in candidates if c.word == "食べる"), None)
        self.assertIsNotNone(taberu_candidate, "Should deinflect 食べた to 食べる")
        if taberu_candidate:
            # Should have Past reason
            has_past = any(
                Reason.Past in chain
                for chain in taberu_candidate.reason_chains
            )
            self.assertTrue(has_past, "Should identify as Past")
    
    def test_deinflect_te_form(self):
        """Test deinflection of te-form (て)."""
        candidates = deinflect("食べて")
        taberu_candidate = next((c for c in candidates if c.word == "食べる"), None)
        self.assertIsNotNone(taberu_candidate, "Should deinflect 食べて to 食べる")
        if taberu_candidate:
            # Should have Te reason
            has_te = any(
                Reason.Te in chain
                for chain in taberu_candidate.reason_chains
            )
            self.assertTrue(has_te, "Should identify as Te form")
    
    def test_deinflect_multiple_reasons(self):
        """Test deinflection with multiple reasons in chain."""
        # 食べていません → 食べる (Continuous + PoliteNegative)
        candidates = deinflect("食べていません")
        taberu_candidate = next((c for c in candidates if c.word == "食べる"), None)
        self.assertIsNotNone(taberu_candidate, "Should deinflect 食べていません to 食べる")
        if taberu_candidate:
            # Should have multiple reasons
            self.assertGreater(len(taberu_candidate.reason_chains), 0)
            # At least one chain should have multiple reasons or contain Continuous
            has_multiple = any(
                len(chain) > 1 or Reason.Continuous in chain
                for chain in taberu_candidate.reason_chains
            )
            self.assertTrue(has_multiple, "Should have multiple reasons or Continuous")
    
    def test_performs_deinflection(self):
        """Test basic deinflection (matches TS test)."""
        result = deinflect('走ります')
        match = next((c for c in result if c.word == '走る'), None)
        self.assertIsNotNone(match)
        self.assertEqual(match.reason_chains, [[Reason.Polite]])
        self.assertEqual(match.type, 2)
        self.assertEqual(match.word, '走る')
    
    def test_performs_deinflection_recursively(self):
        """Test recursive deinflection (matches TS test)."""
        result = deinflect('踊りたくなかった')
        match = next((c for c in result if c.word == '踊る'), None)
        self.assertIsNotNone(match)
        self.assertEqual(match.reason_chains, [[Reason.Tai, Reason.Negative, Reason.Past]])
        self.assertEqual(match.type, 2)
        self.assertEqual(match.word, '踊る')
    
    def test_does_not_allow_duplicates_in_reason_chain(self):
        """Test that duplicate reasons are not allowed (matches TS test)."""
        cases = [
            '見させさせる',  # causative < causative
            '見させてさせる',  # causative < continuous < causative
            '見ていている',  # continuous < continuous
            '見てさせている',  # continuous < causative < continuous
            '見とけとく',  # -te oku < potential < -te oku
        ]
        
        for inflected in cases:
            result = deinflect(inflected)
            match = next((
                c for c in result 
                if c.word == '見る' and (c.type & WordType.IchidanVerb)
            ), None)
            self.assertIsNone(match, f"Should NOT deinflect {inflected} to 見る")
    
    def test_deinflects_kana_variations(self):
        """Test deinflection with kana variations (matches TS test)."""
        cases = [
            ('走ります', '走る', [[Reason.Polite]], 2),
            ('走りまス', '走る', [[Reason.Polite]], 2),
            ('走りマス', '走る', [[Reason.Polite]], 2),
            ('走リマス', '走る', [[Reason.Polite]], 2),
            ('走リマす', '走る', [[Reason.Polite]], 2),
            ('走った', '走る', [[Reason.Past]], 2),
            ('走っタ', '走る', [[Reason.Past]], 2),
            ('走ッタ', '走る', [[Reason.Past]], 2),
            ('走ッた', '走る', [[Reason.Past]], 2),
        ]
        
        for inflected, plain, reason_chains, word_type in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, reason_chains)
            self.assertEqual(match.type, word_type)
            self.assertEqual(match.word, plain)
    
    def test_deinflects_masu_stem_forms(self):
        """Test deinflection of -masu stem forms (matches TS test)."""
        result = deinflect('食べ')
        match = next((c for c in result if c.word == '食べる'), None)
        self.assertIsNotNone(match)
        self.assertEqual(match.reason_chains, [[Reason.MasuStem]])
        self.assertEqual(match.type, WordType.IchidanVerb | WordType.KuruVerb)
        self.assertEqual(match.word, '食べる')
    
    def test_deinflects_nu(self):
        """Test deinflection of -nu form (matches TS test)."""
        cases = [
            ('思わぬ', '思う', 2),
            ('行かぬ', '行く', 2),
            ('話さぬ', '話す', 2),
            ('経たぬ', '経つ', 2),
            ('死なぬ', '死ぬ', 2),
            ('遊ばぬ', '遊ぶ', 2),
            ('止まぬ', '止む', 2),
            ('切らぬ', '切る', 2),
            ('見ぬ', '見る', 9),
            ('こぬ', 'くる', 8),
            ('せぬ', 'する', 16),
        ]
        
        for inflected, plain, word_type in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, [[Reason.Negative]])
            self.assertEqual(match.type, word_type)
            self.assertEqual(match.word, plain)
    
    def test_recursively_deinflects_nu(self):
        """Test recursive deinflection of -nu (matches TS test)."""
        result = deinflect('食べられぬ')
        match = next((c for c in result if c.word == '食べる'), None)
        self.assertIsNotNone(match)
        self.assertEqual(match.reason_chains, [[Reason.PotentialOrPassive, Reason.Negative]])
        self.assertEqual(match.type, 9)
        self.assertEqual(match.word, '食べる')
    
    def test_deinflects_ki_to_kuru(self):
        """Test deinflection of ki to kuru (matches TS test)."""
        result = deinflect('き')
        match = next((c for c in result if c.word == 'くる'), None)
        self.assertIsNotNone(match)
        self.assertEqual(match.reason_chains, [[Reason.MasuStem]])
        self.assertEqual(match.type, 8)
        self.assertEqual(match.word, 'くる')
    
    def test_deinflects_ki_ending_for_i_adj(self):
        """Test deinflection of ki ending for i-adjective (matches TS test)."""
        result = deinflect('美しき')
        match = next((c for c in result if c.word == '美しい'), None)
        self.assertIsNotNone(match)
        self.assertEqual(match.reason_chains, [[Reason.Ki]])
        self.assertEqual(match.type, WordType.IAdj)
        self.assertEqual(match.word, '美しい')
    
    def test_deinflects_all_forms_of_suru(self):
        """Test deinflection of all forms of する (matches TS test)."""
        cases = [
            ('した', [Reason.Past]),
            ('しよう', [Reason.Volitional]),
            ('しない', [Reason.Negative]),
            ('せぬ', [Reason.Negative]),
            ('せん', [Reason.Negative]),
            ('せず', [Reason.Zu]),
            ('される', [Reason.Passive]),
            ('させる', [Reason.Causative]),
            ('しろ', [Reason.Imperative]),
            ('せよ', [Reason.Imperative]),
            ('すれば', [Reason.Ba]),
            ('できる', [Reason.Potential]),
        ]
        
        for inflected, reasons in cases:
            result = deinflect(inflected)
            match = next((
                c for c in result 
                if c.word == 'する' and (c.type & WordType.SuruVerb)
            ), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to する")
            self.assertEqual(match.reason_chains, [reasons])
    
    def test_deinflects_additional_forms_of_special_class_suru_verbs(self):
        """Test deinflection of special class suru-verbs (matches TS test)."""
        cases = [
            ('発する', '発せさせる', [Reason.Irregular, Reason.Causative]),
            ('発する', '発せられる', [Reason.Irregular, Reason.PotentialOrPassive]),
            ('発する', '発しさせる', [Reason.Irregular, Reason.Causative]),
            ('発する', '発しられる', [Reason.Irregular, Reason.PotentialOrPassive]),
            ('発する', '発さない', [Reason.Irregular, Reason.Negative]),
            ('発する', '発さないで', [Reason.Irregular, Reason.NegativeTe]),
            ('発する', '発さず', [Reason.Irregular, Reason.Zu]),
            ('発する', '発そう', [Reason.Irregular, Reason.Volitional]),
            ('愛する', '愛せば', [Reason.Irregular, Reason.Ba]),
            ('愛する', '愛せ', [Reason.Irregular, Reason.Imperative]),
            ('信ずる', '信ぜぬ', [Reason.Irregular, Reason.Negative]),
            ('信ずる', '信ぜず', [Reason.Irregular, Reason.Zu]),
            ('信ずる', '信ぜさせる', [Reason.Irregular, Reason.Causative]),
            ('信ずる', '信ぜられる', [Reason.Irregular, Reason.PotentialOrPassive]),
            ('信ずる', '信ずれば', [Reason.Irregular, Reason.Ba]),
            ('信ずる', '信ぜよ', [Reason.Irregular, Reason.Imperative]),
        ]
        
        for plain, inflected, reasons in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.type, WordType.SpecialSuruVerb)
            self.assertEqual(match.reason_chains, [reasons])
    
    def test_deinflects_irregular_forms_of_iku(self):
        """Test deinflection of irregular forms of 行く (matches TS test)."""
        cases = [
            ('行った', '行く', Reason.Past, 2),
            ('行って', '行く', Reason.Te, 2),
            ('行ったり', '行く', Reason.Tari, 2),
            ('行ったら', '行く', Reason.Tara, 2),
            ('いった', 'いく', Reason.Past, 2),
            ('いって', 'いく', Reason.Te, 2),
            ('いったり', 'いく', Reason.Tari, 2),
            ('いったら', 'いく', Reason.Tara, 2),
            ('逝った', '逝く', Reason.Past, 2),
            ('往った', '往く', Reason.Past, 2),
        ]
        
        for inflected, plain, reason, word_type in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, [[reason]])
            self.assertEqual(match.type, word_type)
            self.assertEqual(match.word, plain)
    
    def test_does_not_deinflect_other_verbs_ending_in_ku_like_iku(self):
        """Test that other verbs ending in く are not deinflected like 行く (matches TS test)."""
        result = deinflect('もどって')
        match = next((c for c in result if c.word == 'もどく'), None)
        self.assertIsNone(match, "Should NOT deinflect もどって to もどく")
    
    def test_deinflects_other_irregular_verbs(self):
        """Test deinflection of other irregular verbs (matches TS test)."""
        cases = [
            ('請うた', '請う'),
            ('乞うた', '乞う'),
            ('恋うた', '恋う'),
            ('こうた', 'こう'),
            ('問うた', '問う'),
            ('とうた', 'とう'),
            ('負うた', '負う'),
            ('おうた', 'おう'),
            ('沿うた', '沿う'),
            ('添うた', '添う'),
            ('副うた', '副う'),
            ('そうた', 'そう'),
            ('厭うた', '厭う'),
            ('いとうた', 'いとう'),
            ('のたまうた', 'のたまう'),
            ('のたもうた', 'のたもう'),
            ('宣うた', '宣う'),
            ('曰うた', '曰う'),
            ('たまうた', 'たまう'),
            ('たもうた', 'たもう'),
            ('給うた', '給う'),
            ('賜うた', '賜う'),
            ('たゆたうた', 'たゆたう'),
            ('たゆとうた', 'たゆとう'),
            ('揺蕩うた', '揺蕩う'),
        ]
        
        for inflected, plain in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, [[Reason.Past]])
            self.assertEqual(match.type, 2)
            self.assertEqual(match.word, plain)
    
    def test_deinflects_continuous_forms_of_other_irregular_verbs(self):
        """Test deinflection of continuous forms of other irregular verbs (matches TS test)."""
        cases = [
            ('請うている', '請う', [Reason.Continuous]),
            ('乞うている', '乞う', [Reason.Continuous]),
            ('恋うている', '恋う', [Reason.Continuous]),
            ('こうてる', 'こう', [Reason.Continuous]),
            ('問うてる', '問う', [Reason.Continuous]),
            ('とうてる', 'とう', [Reason.Continuous]),
            ('負うていた', '負う', [Reason.Continuous, Reason.Past]),
            ('おうていた', 'おう', [Reason.Continuous, Reason.Past]),
            ('沿うていた', '沿う', [Reason.Continuous, Reason.Past]),
            ('添うてた', '添う', [Reason.Continuous, Reason.Past]),
            ('副うてた', '副う', [Reason.Continuous, Reason.Past]),
            ('そうてた', 'そう', [Reason.Continuous, Reason.Past]),
            ('厭うていて', '厭う', [Reason.Continuous, Reason.Te]),
            ('いとうていて', 'いとう', [Reason.Continuous, Reason.Te]),
            ('のたまうている', 'のたまう', [Reason.Continuous]),
            ('のたもうていた', 'のたもう', [Reason.Continuous, Reason.Past]),
            ('宣うてた', '宣う', [Reason.Continuous, Reason.Past]),
            ('曰うてて', '曰う', [Reason.Continuous, Reason.Te]),
            ('たまうている', 'たまう', [Reason.Continuous]),
            ('たもうていた', 'たもう', [Reason.Continuous, Reason.Past]),
            ('給うてた', '給う', [Reason.Continuous, Reason.Past]),
            ('賜うてて', '賜う', [Reason.Continuous, Reason.Te]),
            ('たゆたうている', 'たゆたう', [Reason.Continuous]),
            ('たゆとうていた', 'たゆとう', [Reason.Continuous, Reason.Past]),
            ('揺蕩うてて', '揺蕩う', [Reason.Continuous, Reason.Te]),
        ]
        
        for inflected, plain, reasons in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, [reasons])
            self.assertEqual(match.type, 2)
            self.assertEqual(match.word, plain)
    
    def test_deinflects_gozaru(self):
        """Test deinflection of ござる (matches TS test)."""
        cases = [
            ('ございます', 'ござる', Reason.Polite),
            ('ご座います', 'ご座る', Reason.Polite),
            ('御座います', '御座る', Reason.Polite),
            ('ございません', 'ござる', Reason.PoliteNegative),
            ('ご座いません', 'ご座る', Reason.PoliteNegative),
            ('御座いません', '御座る', Reason.PoliteNegative),
            ('ございませんでした', 'ござる', Reason.PolitePastNegative),
            ('ご座いませんでした', 'ご座る', Reason.PolitePastNegative),
            ('御座いませんでした', '御座る', Reason.PolitePastNegative),
        ]
        
        for inflected, plain, reason in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, [[reason]])
            self.assertEqual(match.word, plain)
    
    def test_deinflects_kudasaru(self):
        """Test deinflection of くださる (matches TS test)."""
        cases = [
            ('くださいます', 'くださる', Reason.Polite),
            ('下さいます', '下さる', Reason.Polite),
            ('くださいません', 'くださる', Reason.PoliteNegative),
            ('下さいません', '下さる', Reason.PoliteNegative),
            ('くださいませんでした', 'くださる', Reason.PolitePastNegative),
            ('下さいませんでした', '下さる', Reason.PolitePastNegative),
        ]
        
        for inflected, plain, reason in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, [[reason]])
            self.assertEqual(match.word, plain)
    
    def test_deinflects_irassharu(self):
        """Test deinflection of いらっしゃる (matches TS test)."""
        cases = [
            ('いらっしゃいます', 'いらっしゃる', [[Reason.Polite]]),
            ('いらっしゃい', 'いらっしゃる', [[Reason.Imperative], [Reason.MasuStem]]),
            ('いらっしゃって', 'いらっしゃる', [[Reason.Te]]),
        ]
        
        for inflected, plain, reason_chains in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            # Check that at least one of the reason chains matches
            found_match = any(
                chain in match.reason_chains for chain in reason_chains
            )
            self.assertTrue(found_match, f"Should have one of {reason_chains} in reason_chains")
    
    def test_deinflects_continuous_form_comprehensive(self):
        """Test deinflection of continuous form comprehensively (matches TS test)."""
        cases = [
            # U-verbs
            ('戻っている', '戻る', 2, None),
            ('戻ってる', '戻る', 2, None),
            ('歩いている', '歩く', 2, None),
            ('歩いてる', '歩く', 2, None),
            ('泳いでいる', '泳ぐ', 2, None),
            ('泳いでる', '泳ぐ', 2, None),
            ('話している', '話す', 2, None),
            ('話してる', '話す', 2, None),
            ('死んでいる', '死ぬ', 2, None),
            ('死んでる', '死ぬ', 2, None),
            ('飼っている', '飼う', 2, None),
            ('飼ってる', '飼う', 2, None),
            ('放っている', '放つ', 2, None),
            ('放ってる', '放つ', 2, None),
            ('遊んでいる', '遊ぶ', 2, None),
            ('遊んでる', '遊ぶ', 2, None),
            ('歩んでいる', '歩む', 2, None),
            ('歩んでる', '歩む', 2, None),
            # Ru-verbs
            ('食べている', '食べる', 9, None),
            ('食べてる', '食べる', 9, None),
            # Special verbs
            ('している', 'する', 16, None),
            ('してる', 'する', 16, None),
            ('来ている', '来る', 9, None),
            ('来てる', '来る', 9, None),
            ('きている', 'くる', 8, None),
            ('きてる', 'くる', 8, None),
            # Combinations
            ('戻っています', '戻る', 2, [Reason.Continuous, Reason.Polite]),
            ('戻ってます', '戻る', 2, [Reason.Continuous, Reason.Polite]),
            ('戻っていない', '戻る', 2, [Reason.Continuous, Reason.Negative]),
            ('戻ってない', '戻る', 2, [Reason.Continuous, Reason.Negative]),
            ('戻っていた', '戻る', 2, [Reason.Continuous, Reason.Past]),
            ('戻ってた', '戻る', 2, [Reason.Continuous, Reason.Past]),
        ]
        
        for inflected, plain, word_type, reasons in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            expected_reasons = [reasons] if reasons else [[Reason.Continuous]]
            self.assertEqual(match.reason_chains, expected_reasons)
            self.assertEqual(match.type, word_type)
            self.assertEqual(match.word, plain)
        
        # Check we don't get false positives
        result = deinflect('食べて')
        match = next((c for c in result if c.word == '食べる'), None)
        self.assertIsNotNone(match)
        # Should not have Continuous as the only reason (it's just Te form)
        has_only_continuous = any(
            chain == [Reason.Continuous] for chain in match.reason_chains
        )
        self.assertFalse(has_only_continuous, "食べて should not have only Continuous reason")
    
    def test_deinflects_respectful_continuous_forms(self):
        """Test deinflection of respectful continuous forms (matches TS test)."""
        cases = [
            ('分かっていらっしゃる', '分かる', [Reason.Respectful, Reason.Continuous]),
            ('分かっていらっしゃい', '分かる', [Reason.Respectful, Reason.Continuous, Reason.Imperative]),
            ('分かってらっしゃる', '分かる', [Reason.Respectful, Reason.Continuous]),
            ('分かってらっしゃい', '分かる', [Reason.Respectful, Reason.Continuous, Reason.Imperative]),
            ('読んでいらっしゃる', '読む', [Reason.Respectful, Reason.Continuous]),
            ('読んでいらっしゃい', '読む', [Reason.Respectful, Reason.Continuous, Reason.Imperative]),
            ('読んでらっしゃる', '読む', [Reason.Respectful, Reason.Continuous]),
            ('読んでらっしゃい', '読む', [Reason.Respectful, Reason.Continuous, Reason.Imperative]),
            ('起きていらっしゃる', '起きる', [Reason.Respectful, Reason.Continuous]),
            ('起きていらっしゃい', '起きる', [Reason.Respectful, Reason.Continuous, Reason.Imperative]),
            ('起きてらっしゃる', '起きる', [Reason.Respectful, Reason.Continuous]),
            ('起きてらっしゃい', '起きる', [Reason.Respectful, Reason.Continuous, Reason.Imperative]),
            ('分かっていらっしゃいます', '分かる', [Reason.Respectful, Reason.Continuous, Reason.Polite]),
            ('分かってらっしゃいます', '分かる', [Reason.Respectful, Reason.Continuous, Reason.Polite]),
            ('分かっていらっしゃって', '分かる', [Reason.Respectful, Reason.Continuous, Reason.Te]),
            ('分かってらっしゃって', '分かる', [Reason.Respectful, Reason.Continuous, Reason.Te]),
        ]
        
        for inflected, plain, reasons in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, [reasons])
    
    def test_deinflects_nasaru_as_respectful_speech_for_suru(self):
        """Test deinflection of なさる as respectful speech for する (matches TS test)."""
        cases = [
            ('なさい', 'なさる', [[Reason.Imperative], [Reason.MasuStem]]),
            ('食べなさい', '食べる', [[Reason.Respectful, Reason.Imperative]]),
            ('帰りなさいませ', '帰る', [[Reason.Respectful, Reason.Polite, Reason.Imperative]]),
            ('仕事なさる', '仕事', [[Reason.SuruNoun, Reason.Respectful]]),
            ('エンジョイなさって', 'エンジョイ', [[Reason.SuruNoun, Reason.Respectful, Reason.Te]]),
            ('喜びなさった', '喜ぶ', [[Reason.Respectful, Reason.Past]]),
        ]
        
        for inflected, plain, reason_chains in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, reason_chains)
    
    def test_deinflects_ni_naru_as_respectful_speech(self):
        """Test deinflection of になる as respectful speech (matches TS test)."""
        cases = [
            ('到着になります', '到着', [Reason.SuruNoun, Reason.Respectful, Reason.Polite]),
            ('読みになります', '読む', [Reason.Respectful, Reason.Polite]),
            ('見えになります', '見える', [Reason.Respectful, Reason.Polite]),
        ]
        
        for inflected, plain, reasons in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, [reasons])
    
    def test_deinflects_humble_or_kansai_dialect_continuous_forms(self):
        """Test deinflection of humble or Kansai dialect continuous forms (matches TS test)."""
        cases = [
            ('行っておる', '行く', [Reason.HumbleOrKansaiDialect, Reason.Continuous]),
            ('行っており', '行く', [Reason.HumbleOrKansaiDialect, Reason.Continuous, Reason.MasuStem]),
            ('行っとる', '行く', [Reason.HumbleOrKansaiDialect, Reason.Continuous]),
            ('行っとり', '行く', [Reason.HumbleOrKansaiDialect, Reason.Continuous, Reason.MasuStem]),
            ('読んでおる', '読む', [Reason.HumbleOrKansaiDialect, Reason.Continuous]),
            ('読んでおり', '読む', [Reason.HumbleOrKansaiDialect, Reason.Continuous, Reason.MasuStem]),
            ('読んどる', '読む', [Reason.HumbleOrKansaiDialect, Reason.Continuous]),
            ('読んどり', '読む', [Reason.HumbleOrKansaiDialect, Reason.Continuous, Reason.MasuStem]),
            ('起きておる', '起きる', [Reason.HumbleOrKansaiDialect, Reason.Continuous]),
            ('起きており', '起きる', [Reason.HumbleOrKansaiDialect, Reason.Continuous, Reason.MasuStem]),
            ('起きとる', '起きる', [Reason.HumbleOrKansaiDialect, Reason.Continuous]),
            ('起きとり', '起きる', [Reason.HumbleOrKansaiDialect, Reason.Continuous, Reason.MasuStem]),
        ]
        
        for inflected, plain, reasons in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, [reasons])
    
    def test_deinflects_itasu_as_humble_speech_for_suru(self):
        """Test deinflection of 致す as humble speech for する (matches TS test)."""
        cases = [
            ('お願いいたします', 'お願い', [Reason.SuruNoun, Reason.Humble, Reason.Polite]),
            ('お願い致します', 'お願い', [Reason.SuruNoun, Reason.Humble, Reason.Polite]),
            ('待ちいたします', '待つ', [Reason.Humble, Reason.Polite]),
            ('待ち致します', '待つ', [Reason.Humble, Reason.Polite]),
            ('食べいたします', '食べる', [Reason.Humble, Reason.Polite]),
            ('食べ致します', '食べる', [Reason.Humble, Reason.Polite]),
        ]
        
        for inflected, plain, reasons in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, [reasons])
    
    def test_deinflects_zaru_wo_enai(self):
        """Test deinflection of ざるを得ない (matches TS test)."""
        cases = [
            ('闘わざるを得なかった', '闘う'),
            ('闘わざるをえなかった', '闘う'),
            ('やらざるを得ぬ', 'やる'),
            ('やらざるをえぬ', 'やる'),
            ('闘わざる得なかった', '闘う'),
            ('闘わざるえなかった', '闘う'),
            ('やらざる得ぬ', 'やる'),
            ('やらざるえぬ', 'やる'),
        ]
        
        for inflected, plain in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            # The ざるを得ない reason should be the first one in the list
            self.assertEqual(match.reason_chains[0][0], Reason.ZaruWoEnai)
    
    def test_deinflects_naide(self):
        """Test deinflection of ないで (matches TS test)."""
        cases = [
            ('遊ばないで', '遊ぶ'),
            ('やらないで', 'やる'),
            ('食べないで', '食べる'),
            ('しないで', 'する'),
            ('こないで', 'くる'),
            ('来ないで', '来る'),
        ]
        
        for inflected, plain in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains[0][0], Reason.NegativeTe)
    
    def test_deinflects_eru_uru(self):
        """Test deinflection of -得る (matches TS test)."""
        cases = [
            ('し得る', 'する'),
            ('しえる', 'する'),
            ('しうる', 'する'),
            ('来得る', '来る'),
            ('あり得る', 'ある'),
            ('考え得る', '考える'),
        ]
        
        for inflected, plain in cases:
            result = deinflect(inflected)
            match = next((c for c in result if c.word == plain), None)
            self.assertIsNotNone(match, f"Should deinflect {inflected} to {plain}")
            self.assertEqual(match.reason_chains, [[Reason.EruUru]])


if __name__ == '__main__':
    unittest.main()

