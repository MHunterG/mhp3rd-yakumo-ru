"""Public format and resumable translation contracts over invented strings."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.langfile import Language, identity, loads, read, validate, write
from tools.translate import decoded_rows, main, payload_for


class LanguageTests(unittest.TestCase):
    def test_mixed_keys_round_trip(self):
        language = Language('ru', 'Russian', {
            (4059, 64, 136): 'Exact', (4059, 64, '*'): 'Portable', (16, 2, 1): 'Menu',
        })
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / 'ru.lang'
            write(output, language)
            self.assertEqual(read(output), language)
            self.assertLess(output.read_text().index('64:*'), output.read_text().index('64:136'))

    def test_duplicate_and_invalid_keys(self):
        for key in ('*:*', '*:1', '64:1-2', '-1:*', '65536:*', '64:4294967296', '64:*.'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                loads('language=ru\nname=Russian\n[4059]\n' + key + '=Text\n')
        with self.assertRaises(ValueError):
            loads('language=ru\nname=Russian\n[4059]\n64:*=First\n64:*=Second\n')
        self.assertEqual(identity('4294967295:65535:*'), (4294967295, 65535, '*'))
        with self.assertRaises(ValueError):
            identity('4294967296:64:*')

    def test_formatting_validation_for_wildcards(self):
        source = Language('ja', 'Japanese', {(4059, 64, '*'): 'Invented ~C01\nsecond'})
        good = Language('ru', 'Russian', {(4059, 64, '*'): 'Translated ~C01\nsecond'})
        self.assertEqual(validate(source, good), [])
        bad = Language('ru', 'Russian', {(4059, 64, '*'): 'Lost formatting'})
        self.assertTrue(validate(source, bad))

    def test_api_round_trip_preserves_mixed_identities(self):
        source = Language('ja', 'Japanese', {
            (4059, 64, '*'): 'Invented ~C01\nsecond', (4059, 64, 136): 'Exact',
        })
        payload, protected = payload_for(source, list(source.rows), 'Russian', 'synthetic-model', 32)
        values = json.loads(payload['messages'][1]['content'])['strings']
        response = {'choices': [{'finish_reason': 'stop', 'message': {
            'content': json.dumps({'translations': values})}}]}
        self.assertEqual(decoded_rows(response, protected), source.rows)
        values['4059:64:*'] = 'Dropped markers'
        response['choices'][0]['message']['content'] = json.dumps({'translations': values})
        with self.assertRaises(ValueError):
            decoded_rows(response, protected)

    def test_resume_preserves_completed_reference_wildcard(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'synthetic-key'}):
            source, output = Path(root) / 'source.lang', Path(root) / 'ru.lang'
            language = Language('ja', 'Japanese', {
                (4059, 64, '*'): 'Portable', (4059, 64, 136): 'Exact', (16, 2, 1): 'Menu',
            })
            write(source, language)
            write(output, Language('ru', 'Russian', {(4059, 64, '*'): 'Completed'}))
            calls = []

            def client(payload, _key):
                values = json.loads(payload['messages'][1]['content'])['strings']
                calls.extend(values)
                return {'choices': [{'finish_reason': 'stop', 'message': {
                    'content': json.dumps({'translations': {k: 'Translated ' + v for k, v in values.items()}})}}]}

            args = ['--source', str(source), '--output', str(output), '--language', 'ru', '--name', 'Russian',
                    '--batch-size', '1', '--execute']
            self.assertEqual(main(args + ['--max-batches', '1'], client=client), 0)
            self.assertEqual(len(read(output).rows), 2)
            self.assertEqual(main(args, client=client), 0)
            self.assertEqual(set(read(output).rows), set(language.rows))
            self.assertEqual(read(output).rows[4059, 64, '*'], 'Completed')
            self.assertNotIn('4059:64:*', calls)
            self.assertEqual(len(calls), 2)


if __name__ == '__main__':
    unittest.main()
