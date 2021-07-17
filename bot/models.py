import asyncio
import asyncpg

import pg_orm
from pg_orm import models  # A module made by me :) https://github.com/Rashaad1268/Postgresql-Python-ORM
from pg_orm import errors
from discord.ext import commands

from bot.constants import Postgres

run = asyncio.get_event_loop().run_until_complete

pool = run(asyncpg.create_pool(Postgres.uri))
Model = models.create_async_model(pool)


class Members(Model):
    id = models.IntegerField(unique=True, big_int=True)
    name = models.CharField(33)
    discriminator = models.CharField(4)
    joined_at = models.DateTimeField()
    in_guild = models.BooleanField()
    total_infractions = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name}#{self.discriminator}"

class Messages(Model):
    id = models.IntegerField(unique=True, big_int=True)
    author = models.ForeignKey(Members, on_delete=models.CASCADE, sql_type="BIGINT")
    channel_id = models.IntegerField(big_int=True)
    content = models.TextField()
    sent_at = models.DateTimeField()


class Bans(Model):
    member = models.ForeignKey(Members, on_delete=models.CASCADE, sql_type="BIGINT")
    reason = models.TextField(null=True)
    given_at = models.DateTimeField()
    expiry = models.DateTimeField(null=True)


class Mutes(Model):
    member = models.ForeignKey(Members, on_delete=models.CASCADE, sql_type="BIGINT")
    reason = models.TextField(null=True)
    given_at = models.DateTimeField()
    expiry = models.DateTimeField(null=True)


class Warns(Model):
    member = models.ForeignKey(Members, on_delete=models.CASCADE, sql_type="BIGINT")
    reason = models.TextField(null=True)
    given_at = models.DateTimeField()
    expiry = models.DateTimeField(null=True)


class Tags(Model):
    tag_name = models.CharField(20)
    content = models.TextField()
    author = models.ForeignKey(Members, on_delete=models.CASCADE, sql_type="BIGINT")


class OffTopicNames(Model):
    name = models.CharField(50, unique=True)
    author = models.ForeignKey(Members, on_delete=models.CASCADE, sql_type="BIGINT")
    date_added = models.DateTimeField()

    def __str__(self):
        return self.name


class DataBase(object):
    def __init__(self):
        self.execute = Model.db.execute
        self.fetch = Model.db.fetch
        self.fetchrow = Model.db.fetchrow
        self.fetchval = Model.db.fetchval

        for model in Model.subclasses():
            setattr(self, model.__name__.lower(), model)


# async def init(pool):
#     await pg_orm.migrations.apply_async_migrations(pool)


    async def close(self):
        await pool.close()
