import hashlib
from database import get_db
from utils import to_json, utc_now_str


class Blockchain:
    def __init__(self):
        self._ensure_genesis()

    def _ensure_genesis(self):
        db = get_db()
        exists = db.execute('SELECT 1 FROM blocks LIMIT 1').fetchone()
        if not exists:
            self._insert_block(0, {'type': 'genesis'}, '0')
        db.close()

    def _hash_payload(self, index: int, timestamp: str, data_json: str, previous_hash: str) -> str:
        payload = f'{index}|{timestamp}|{data_json}|{previous_hash}'
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def _insert_block(self, block_index: int, data: dict, previous_hash: str) -> str:
        db = get_db()
        timestamp = utc_now_str()
        data_json = to_json(data)
        current_hash = self._hash_payload(block_index, timestamp, data_json, previous_hash)
        db.execute(
            'INSERT INTO blocks (block_index, timestamp, data_json, previous_hash, current_hash) VALUES (?, ?, ?, ?, ?)',
            (block_index, timestamp, data_json, previous_hash, current_hash)
        )
        db.commit()
        db.close()
        return current_hash

    def add_vote_block(self, data: dict) -> str:
        db = get_db()
        row = db.execute('SELECT block_index, current_hash FROM blocks ORDER BY block_index DESC LIMIT 1').fetchone()
        db.close()
        next_index = row['block_index'] + 1
        return self._insert_block(next_index, data, row['current_hash'])

    def get_chain(self):
        db = get_db()
        rows = db.execute('SELECT block_index, timestamp, data_json, previous_hash, current_hash FROM blocks ORDER BY block_index ASC').fetchall()
        db.close()
        return rows

    def is_valid(self) -> bool:
        chain = self.get_chain()
        previous_hash = '0'
        previous_index = 0
        for row in chain:
            recalculated = self._hash_payload(row['block_index'], row['timestamp'], row['data_json'], row['previous_hash'])
            if row['current_hash'] != recalculated:
                return False
            if row['block_index'] == 0:
                previous_hash = row['current_hash']
                continue
            if row['previous_hash'] != previous_hash:
                return False
            if row['block_index'] != previous_index + 1:
                return False
            previous_hash = row['current_hash']
            previous_index = row['block_index']
        return True
