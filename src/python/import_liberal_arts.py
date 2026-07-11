#!/usr/bin/env python3
import sqlite3
import json
import hashlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database_schema_base import EnhancedDatabaseManager
from database_schema import SCHEMA
from liberal_arts_data import (
    POEMS, CLASSICAL_CHINESE, TEXTBOOK_SEGMENTS,
    IDIOMS, XIEHOUYU, LITERATURE_SEGMENTS,
    READING_COMPREHENSION, FAMOUS_QUOTES
)


LIBERAL_ARTS_TABLES_SQL = '''
CREATE TABLE IF NOT EXISTS poems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    poem_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    dynasty TEXT NOT NULL,
    content TEXT NOT NULL,
    pinyin TEXT,
    translation TEXT,
    annotation TEXT,
    appreciation TEXT,
    genre TEXT,
    theme TEXT,
    grade_level TEXT,
    requirement TEXT DEFAULT 'recite',
    difficulty INTEGER DEFAULT 3,
    is_classic INTEGER DEFAULT 1,
    tags TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_poems_poem_id ON poems(poem_id);
CREATE INDEX IF NOT EXISTS idx_poems_title ON poems(title);
CREATE INDEX IF NOT EXISTS idx_poems_author ON poems(author);
CREATE INDEX IF NOT EXISTS idx_poems_dynasty ON poems(dynasty);
CREATE INDEX IF NOT EXISTS idx_poems_grade_level ON poems(grade_level);
CREATE INDEX IF NOT EXISTS idx_poems_genre ON poems(genre);
CREATE INDEX IF NOT EXISTS idx_poems_is_classic ON poems(is_classic);

CREATE TABLE IF NOT EXISTS classical_chinese (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    dynasty TEXT,
    original_text TEXT NOT NULL,
    modern_translation TEXT,
    word_notes TEXT,
    sentence_analysis TEXT,
    grammar_points TEXT,
    cultural_context TEXT,
    grade_level TEXT,
    requirement TEXT DEFAULT 'understand',
    difficulty INTEGER DEFAULT 4,
    is_classic INTEGER DEFAULT 1,
    tags TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_classical_chinese_article_id ON classical_chinese(article_id);
CREATE INDEX IF NOT EXISTS idx_classical_chinese_title ON classical_chinese(title);
CREATE INDEX IF NOT EXISTS idx_classical_chinese_author ON classical_chinese(author);
CREATE INDEX IF NOT EXISTS idx_classical_chinese_dynasty ON classical_chinese(dynasty);
CREATE INDEX IF NOT EXISTS idx_classical_chinese_grade_level ON classical_chinese(grade_level);
CREATE INDEX IF NOT EXISTS idx_classical_chinese_is_classic ON classical_chinese(is_classic);

CREATE TABLE IF NOT EXISTS textbook_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    source TEXT,
    content TEXT NOT NULL,
    summary TEXT,
    key_points TEXT,
    writing_style TEXT,
    analysis TEXT,
    subject TEXT DEFAULT 'chinese',
    grade_level TEXT,
    requirement TEXT DEFAULT 'master',
    difficulty INTEGER DEFAULT 3,
    tags TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_textbook_segments_segment_id ON textbook_segments(segment_id);
CREATE INDEX IF NOT EXISTS idx_textbook_segments_title ON textbook_segments(title);
CREATE INDEX IF NOT EXISTS idx_textbook_segments_author ON textbook_segments(author);
CREATE INDEX IF NOT EXISTS idx_textbook_segments_subject ON textbook_segments(subject);
CREATE INDEX IF NOT EXISTS idx_textbook_segments_grade_level ON textbook_segments(grade_level);

CREATE TABLE IF NOT EXISTS idioms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idiom_id TEXT UNIQUE NOT NULL,
    idiom TEXT NOT NULL,
    pinyin TEXT,
    meaning TEXT NOT NULL,
    story TEXT,
    origin TEXT,
    part_of_speech TEXT,
    usage TEXT,
    synonyms TEXT,
    antonyms TEXT,
    difficulty INTEGER DEFAULT 3,
    is_common INTEGER DEFAULT 1,
    grade_level TEXT,
    tags TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_idioms_idiom_id ON idioms(idiom_id);
CREATE INDEX IF NOT EXISTS idx_idioms_idiom ON idioms(idiom);
CREATE INDEX IF NOT EXISTS idx_idioms_is_common ON idioms(is_common);
CREATE INDEX IF NOT EXISTS idx_idioms_grade_level ON idioms(grade_level);

CREATE TABLE IF NOT EXISTS xiehouyu (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    xhy_id TEXT UNIQUE NOT NULL,
    front_part TEXT NOT NULL,
    back_part TEXT NOT NULL,
    pinyin TEXT,
    meaning TEXT,
    usage TEXT,
    difficulty INTEGER DEFAULT 2,
    is_common INTEGER DEFAULT 1,
    grade_level TEXT,
    tags TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_xiehouyu_xhy_id ON xiehouyu(xhy_id);
CREATE INDEX IF NOT EXISTS idx_xiehouyu_front_part ON xiehouyu(front_part);
CREATE INDEX IF NOT EXISTS idx_xiehouyu_is_common ON xiehouyu(is_common);
CREATE INDEX IF NOT EXISTS idx_xiehouyu_grade_level ON xiehouyu(grade_level);

CREATE TABLE IF NOT EXISTS literature_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    work TEXT,
    content TEXT NOT NULL,
    summary TEXT,
    analysis TEXT,
    literary_device TEXT,
    theme TEXT,
    origin_country TEXT DEFAULT '中国',
    time_period TEXT,
    grade_level TEXT,
    difficulty INTEGER DEFAULT 4,
    is_classic INTEGER DEFAULT 1,
    tags TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_literature_segments_segment_id ON literature_segments(segment_id);
CREATE INDEX IF NOT EXISTS idx_literature_segments_title ON literature_segments(title);
CREATE INDEX IF NOT EXISTS idx_literature_segments_author ON literature_segments(author);
CREATE INDEX IF NOT EXISTS idx_literature_segments_origin_country ON literature_segments(origin_country);
CREATE INDEX IF NOT EXISTS idx_literature_segments_is_classic ON literature_segments(is_classic);
CREATE INDEX IF NOT EXISTS idx_literature_segments_grade_level ON literature_segments(grade_level);

CREATE TABLE IF NOT EXISTS reading_comprehension (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rc_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    article TEXT NOT NULL,
    questions TEXT,
    answers TEXT,
    analysis TEXT,
    genre TEXT,
    subject TEXT DEFAULT 'chinese',
    grade_level TEXT,
    difficulty INTEGER DEFAULT 3,
    time_limit INTEGER,
    score INTEGER,
    tags TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reading_comprehension_rc_id ON reading_comprehension(rc_id);
CREATE INDEX IF NOT EXISTS idx_reading_comprehension_title ON reading_comprehension(title);
CREATE INDEX IF NOT EXISTS idx_reading_comprehension_genre ON reading_comprehension(genre);
CREATE INDEX IF NOT EXISTS idx_reading_comprehension_subject ON reading_comprehension(subject);
CREATE INDEX IF NOT EXISTS idx_reading_comprehension_grade_level ON reading_comprehension(grade_level);
CREATE INDEX IF NOT EXISTS idx_reading_comprehension_difficulty ON reading_comprehension(difficulty);

CREATE TABLE IF NOT EXISTS famous_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote_id TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    author TEXT NOT NULL,
    source TEXT,
    category TEXT,
    language TEXT DEFAULT 'chinese',
    grade_level TEXT,
    difficulty INTEGER DEFAULT 2,
    is_classic INTEGER DEFAULT 1,
    tags TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_famous_quotes_quote_id ON famous_quotes(quote_id);
CREATE INDEX IF NOT EXISTS idx_famous_quotes_author ON famous_quotes(author);
CREATE INDEX IF NOT EXISTS idx_famous_quotes_category ON famous_quotes(category);
CREATE INDEX IF NOT EXISTS idx_famous_quotes_language ON famous_quotes(language);
CREATE INDEX IF NOT EXISTS idx_famous_quotes_is_classic ON famous_quotes(is_classic);
CREATE INDEX IF NOT EXISTS idx_famous_quotes_grade_level ON famous_quotes(grade_level);
'''


class LiberalArtsImporter:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(LIBERAL_ARTS_TABLES_SQL)
        self.conn.commit()
        print("✅ 文科知识表创建完成")

    def close(self):
        if self.conn:
            self.conn.close()

    def _generate_id(self, text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:16]

    def _insert_poem(self, poem):
        poem_id = self._generate_id(poem['title'] + poem['author'])
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO poems (
                    poem_id, title, author, dynasty, content, pinyin,
                    translation, annotation, appreciation, genre, theme,
                    grade_level, requirement, difficulty, is_classic, tags,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                poem_id, poem['title'], poem['author'], poem['dynasty'],
                poem['content'], poem.get('pinyin', ''), poem.get('translation', ''),
                poem.get('annotation', ''), '', poem['genre'], poem['theme'],
                poem['grade_level'], poem['requirement'], poem['difficulty'],
                poem['is_classic'], json.dumps(poem.get('tags', [])),
                int(poem.get('created_at', 0)) or 1625078400,
                int(poem.get('updated_at', 0)) or 1625078400
            ))
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error inserting poem '{poem['title']}': {e}")
            return False

    def _insert_classical_chinese(self, item):
        article_id = self._generate_id(item['title'] + item['author'])
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO classical_chinese (
                    article_id, title, author, dynasty, original_text,
                    modern_translation, word_notes, sentence_analysis,
                    grammar_points, cultural_context, grade_level,
                    requirement, difficulty, is_classic, tags,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article_id, item['title'], item['author'], item['dynasty'],
                item['original_text'], item['modern_translation'],
                json.dumps(item.get('word_notes', {})),
                json.dumps(item.get('sentence_analysis', [])),
                json.dumps(item.get('grammar_points', [])),
                item.get('cultural_context', ''),
                item['grade_level'], item['requirement'], item['difficulty'],
                item['is_classic'], json.dumps(item.get('tags', [])),
                1625078400, 1625078400
            ))
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error inserting classical chinese '{item['title']}': {e}")
            return False

    def _insert_textbook_segment(self, segment):
        segment_id = self._generate_id(segment['title'] + segment['author'])
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO textbook_segments (
                    segment_id, title, author, source, content, summary,
                    key_points, writing_style, analysis, subject, grade_level,
                    requirement, difficulty, tags, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                segment_id, segment['title'], segment['author'], segment['source'],
                segment['content'], segment['summary'],
                json.dumps(segment.get('key_points', [])),
                segment.get('writing_style', ''), segment.get('analysis', ''),
                segment['subject'], segment['grade_level'], segment['requirement'],
                segment['difficulty'], json.dumps(segment.get('tags', [])),
                1625078400, 1625078400
            ))
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error inserting textbook segment '{segment['title']}': {e}")
            return False

    def _insert_idiom(self, idiom):
        idiom_id = self._generate_id(idiom['idiom'])
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO idioms (
                    idiom_id, idiom, pinyin, meaning, story, origin,
                    part_of_speech, usage, synonyms, antonyms,
                    difficulty, is_common, grade_level, tags,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                idiom_id, idiom['idiom'], idiom['pinyin'], idiom['meaning'],
                idiom.get('story', ''), idiom.get('origin', ''),
                idiom.get('part_of_speech', ''), idiom.get('usage', ''),
                json.dumps(idiom.get('synonyms', [])),
                json.dumps(idiom.get('antonyms', [])),
                idiom['difficulty'], idiom['is_common'], idiom['grade_level'],
                json.dumps(idiom.get('tags', [])),
                1625078400, 1625078400
            ))
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error inserting idiom '{idiom['idiom']}': {e}")
            return False

    def _insert_xiehouyu(self, item):
        xhy_id = self._generate_id(item['front_part'] + item['back_part'])
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO xiehouyu (
                    xhy_id, front_part, back_part, pinyin, meaning, usage,
                    difficulty, is_common, grade_level, tags,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                xhy_id, item['front_part'], item['back_part'],
                item.get('pinyin', ''), item['meaning'], item.get('usage', ''),
                item['difficulty'], item['is_common'], item['grade_level'],
                json.dumps(item.get('tags', [])),
                1625078400, 1625078400
            ))
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error inserting xiehouyu '{item['front_part']}': {e}")
            return False

    def _insert_literature_segment(self, segment):
        segment_id = self._generate_id(segment['title'] + segment['author'])
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO literature_segments (
                    segment_id, title, author, work, content, summary,
                    analysis, literary_device, theme, origin_country,
                    time_period, grade_level, difficulty, is_classic, tags,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                segment_id, segment['title'], segment['author'], segment['work'],
                segment['content'], segment['summary'], segment.get('analysis', ''),
                segment.get('literary_device', ''), segment.get('theme', ''),
                segment.get('origin_country', '中国'), segment.get('time_period', ''),
                segment['grade_level'], segment['difficulty'], segment['is_classic'],
                json.dumps(segment.get('tags', [])),
                1625078400, 1625078400
            ))
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error inserting literature segment '{segment['title']}': {e}")
            return False

    def _insert_reading_comprehension(self, item):
        rc_id = self._generate_id(item['title'] + item['article'][:50])
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO reading_comprehension (
                    rc_id, title, article, questions, answers, analysis,
                    genre, subject, grade_level, difficulty, time_limit,
                    score, tags, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rc_id, item['title'], item['article'],
                json.dumps(item.get('questions', [])),
                json.dumps(item.get('answers', [])),
                json.dumps(item.get('analysis', [])),
                item.get('genre', ''), item.get('subject', 'chinese'),
                item['grade_level'], item['difficulty'], item.get('time_limit', 15),
                item.get('score', 10), json.dumps(item.get('tags', [])),
                1625078400, 1625078400
            ))
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error inserting reading comprehension '{item['title']}': {e}")
            return False

    def _insert_famous_quote(self, quote):
        quote_id = self._generate_id(quote['content'] + quote['author'])
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO famous_quotes (
                    quote_id, content, author, source, category, language,
                    grade_level, difficulty, is_classic, tags,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                quote_id, quote['content'], quote['author'], quote.get('source', ''),
                quote.get('category', ''), quote.get('language', 'chinese'),
                quote['grade_level'], quote['difficulty'], quote['is_classic'],
                json.dumps(quote.get('tags', [])),
                1625078400, 1625078400
            ))
            return self.cursor.rowcount > 0
        except Exception as e:
            print(f"Error inserting famous quote '{quote['content'][:20]}...': {e}")
            return False

    def import_all(self):
        self.connect()
        try:
            counts = {}

            counts['poems'] = sum(1 for p in POEMS if self._insert_poem(p))
            self.conn.commit()
            print(f"Inserted {counts['poems']} poems")

            counts['classical_chinese'] = sum(1 for c in CLASSICAL_CHINESE if self._insert_classical_chinese(c))
            self.conn.commit()
            print(f"Inserted {counts['classical_chinese']} classical chinese articles")

            counts['textbook_segments'] = sum(1 for t in TEXTBOOK_SEGMENTS if self._insert_textbook_segment(t))
            self.conn.commit()
            print(f"Inserted {counts['textbook_segments']} textbook segments")

            counts['idioms'] = sum(1 for i in IDIOMS if self._insert_idiom(i))
            self.conn.commit()
            print(f"Inserted {counts['idioms']} idioms")

            counts['xiehouyu'] = sum(1 for x in XIEHOUYU if self._insert_xiehouyu(x))
            self.conn.commit()
            print(f"Inserted {counts['xiehouyu']} xiehouyu")

            counts['literature_segments'] = sum(1 for l in LITERATURE_SEGMENTS if self._insert_literature_segment(l))
            self.conn.commit()
            print(f"Inserted {counts['literature_segments']} literature segments")

            counts['reading_comprehension'] = sum(1 for r in READING_COMPREHENSION if self._insert_reading_comprehension(r))
            self.conn.commit()
            print(f"Inserted {counts['reading_comprehension']} reading comprehension exercises")

            counts['famous_quotes'] = sum(1 for f in FAMOUS_QUOTES if self._insert_famous_quote(f))
            self.conn.commit()
            print(f"Inserted {counts['famous_quotes']} famous quotes")

            print("\nImport completed successfully!")
            print("Summary:")
            for table, count in counts.items():
                print(f"  {table}: {count} records")

            return counts

        except Exception as e:
            self.conn.rollback()
            print(f"Error during import: {e}")
            raise
        finally:
            self.close()


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, 'flask-app', 'mtscos.db')

    importer = LiberalArtsImporter(db_path)
    importer.import_all()


if __name__ == '__main__':
    main()
