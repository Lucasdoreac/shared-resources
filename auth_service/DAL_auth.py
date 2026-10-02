import hmac
from datetime import datetime
from BaseRepository import BaseRepository


class AuthenticationRepository(BaseRepository):
    """
        Repositório responsável por gerenciar as operações de autenticação no banco de dados.

        Este repositório utiliza a coleção 'authentications' para armazenar os registros de autenticação,
        e implementa métodos para inserir e validar esses registros.
    """


    def get_collection_name(self):
        """
                Retorna a coleção do MongoDB utilizada para armazenar os registros de autenticação.

                Returns:
                    Collection: A coleção 'authentications' do banco de dados.
        """

        return self.db.authentications

    MAX_ACTIVE_PER_EMAIL = 5

    def insert_authentication(self, email, token_hash, expires_at, kind="link"):
        """Store the hash of a token of ``kind`` ("link" or "session") for ``email``.

        Expired records and all but the newest MAX_ACTIVE_PER_EMAIL - 1 of that
        kind are removed first, so repeated requests cannot grow the collection.
        """
        collection = self.get_collection_name()
        now = datetime.now()
        collection.delete_many({"email": email, "kind": kind, "expiresAt": {"$lte": now}})
        live = list(collection.find({"email": email, "kind": kind}, {"_id": 1}).sort("createdAt", -1))
        stale = [doc["_id"] for doc in live[self.MAX_ACTIVE_PER_EMAIL - 1:]]
        if stale:
            collection.delete_many({"_id": {"$in": stale}})
        record = {
            "email": email,
            "kind": kind,
            "tokenHash": token_hash,
            "createdAt": now,
            "expiresAt": expires_at,
        }
        return collection.insert_one(record).inserted_id

    def _matching_record(self, email, token_hash, kind):
        candidates = self.get_collection_name().find(
            {"email": email, "kind": kind, "expiresAt": {"$gt": datetime.now()}},
            {"tokenHash": 1},
        ).limit(self.MAX_ACTIVE_PER_EMAIL * 2)
        match = None
        for record in candidates:  # no early exit: constant-time per candidate
            if hmac.compare_digest(str(record.get("tokenHash", "")), token_hash):
                match = record
        return match

    def validate_authentication(self, email, token_hash, kind="session"):
        """True when a live ``kind`` record for ``email`` holds ``token_hash``."""
        return self._matching_record(email, token_hash, kind) is not None

    def consume_authentication(self, email, token_hash, kind="link"):
        """Single use: delete the matching record and report whether this call won it.

        The delete is the claim, so two simultaneous requests with the same
        token cannot both succeed.
        """
        match = self._matching_record(email, token_hash, kind)
        if match is None:
            return False
        return self.get_collection_name().delete_one({"_id": match["_id"]}).deleted_count == 1
