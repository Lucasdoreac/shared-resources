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

    def insert_authentication(self, email, token_hash, expires_at):
        """Store the hash of a login token for ``email``; keeps few live tokens per address.

        Expired records and all but the newest MAX_ACTIVE_PER_EMAIL - 1 are
        removed first, so repeated link requests cannot grow the collection.
        """
        collection = self.get_collection_name()
        now = datetime.now()
        collection.delete_many({"email": email, "expiresAt": {"$lte": now}})
        live = list(collection.find({"email": email}, {"_id": 1}).sort("createdAt", -1))
        stale = [doc["_id"] for doc in live[self.MAX_ACTIVE_PER_EMAIL - 1:]]
        if stale:
            collection.delete_many({"_id": {"$in": stale}})
        record = {
            "email": email,
            "tokenHash": token_hash,
            "createdAt": now,
            "expiresAt": expires_at,
        }
        return collection.insert_one(record).inserted_id

    def validate_authentication(self, email, token_hash):
        """True when a non-expired record for ``email`` holds ``token_hash``.

        Records are looked up by e-mail and compared in constant time; records
        written in the old format (no ``tokenHash``) never match.
        """
        candidates = self.get_collection_name().find(
            {"email": email, "expiresAt": {"$gt": datetime.now()}, "tokenHash": {"$exists": True}},
            {"tokenHash": 1},
        ).limit(self.MAX_ACTIVE_PER_EMAIL * 2)
        matched = False
        for record in candidates:
            if hmac.compare_digest(str(record.get("tokenHash", "")), token_hash):
                matched = True
        return matched
