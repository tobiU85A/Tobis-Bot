import os
from dotenv import load_dotenv
import mysql.connector

import discord
from discord.ext import commands
from discord.commands import slash_command, Option

dc_id = os.getenv('DC_ID')
db_servers_table = os.getenv('MYSQL_SERVERS_TABLE')
db_users_table = os.getenv('MYSQL_USERS_TABLE')
db_key = os.getenv('MYSQL_KEY')

def sql_logon():
        global db_connection, db_cursor 

        db_connection = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST'),
            user=os.environ.get('MYSQL_USER'),
            passwd=os.environ.get('MYSQL_PASSWORD'),
            database=os.environ.get('MYSQL_DATABASE')
        )
        db_cursor = db_connection.cursor()
sql_logon()


class COUNT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.count_channel_id = None
        self.expected_value = None
        self.last_author = None

    db_check_server_count = f"SELECT Count FROM {db_servers_table} WHERE ServerID = %s;"
    db_cursor.execute(db_check_server_count, (dc_id,))
    db_count = db_cursor.fetchall()

    if not db_count:
        db_create_entry = f"INSERT INTO {db_servers_table} (ServerID, Count, Saves) VALUES ({dc_id}, 0, 0);"
        db_cursor.execute(db_create_entry)
        db_connection.commit()

    try:
        if int(db_count[0][0]) > 0:
            start_value = int(db_count[0][0]) + 1

    except:
        start_value = 1

    # Creates the slash command with the parameters channel and start value.
    @slash_command(name="count", description="Start a count in a channel.")
    async def count(
            self,
            ctx,
            channel: Option(discord.TextChannel, "The count will be started in this channel."), # type: ignore
            start_value: Option(int, "Define where the count begins.", min_value=1, default=start_value) # type: ignore
    ):
        self.count_channel_id = channel.id
        self.expected_value = start_value

        await channel.send(f"{ctx.author.mention} started a count in this channel. The count begins at {start_value}.")
        await ctx.respond(f"The count was started in <#{channel.id}>.", ephemeral=True)

    # Waits for messages and checks if the input is equal to the expected value.
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != self.count_channel_id or message.author.bot:
            return

        try:
            server_count = int(message.content)
            user_id = message.author.id

            db_check_user = f"SELECT user_id FROM count_users WHERE user_id = aes_encrypt('{user_id}','{db_key}')"
            db_cursor.execute(db_check_user)
            db_user = db_cursor.fetchall()

            if not db_user:
                db_add_user = f"INSERT INTO {db_users_table}(user_id, count, saves) VALUES (aes_encrypt('{user_id}', '{db_key}'), 0, 1);"
                db_cursor.execute(db_add_user)
                db_connection.commit()

                await message.reply(f"{message.author.mention} you're new here right?\n"
                                    f"Therefore you will get a free User Save. 😁\n"
                                    f"Don't waste it!")

            if server_count == self.expected_value and message.author != self.last_author:
                await message.add_reaction("✅")

                db_update_server_count = f"UPDATE {db_servers_table} SET Count = %s WHERE ServerID = %s;"
                db_cursor.execute(db_update_server_count, (self.expected_value, dc_id))

                db_update_user_count = f"UPDATE {db_users_table} SET count = count + 1 WHERE user_id = aes_encrypt('{user_id}','{db_key}');"
                db_cursor.execute(db_update_user_count)
                db_connection.commit()
                self.expected_value += 1

                db_check_user_count = f"SELECT count FROM {db_users_table} WHERE user_id = aes_encrypt('{user_id}','{db_key}')"
                db_cursor.execute(db_check_user_count)
                user_count = db_cursor.fetchall()

                if int(user_count[0][0]) % 30 == 0:
                    db_update_user_saves = f"UPDATE {db_users_table} SET saves = saves + 1 WHERE user_id = aes_encrypt('{user_id}','{db_key}');"
                    db_cursor.execute(db_update_user_saves)
                    db_connection.commit()

                    db_check_user_saves = f"SELECT saves FROM {db_users_table} WHERE user_id = aes_encrypt('{user_id}','{db_key}');"
                    db_cursor.execute(db_check_user_saves)
                    user_saves = db_cursor.fetchall()

                    await message.reply(f"{message.author.mention} you counted {user_count[0][0]} times correctly.\n"
                                        "Therefore you will get a User Save. 😎\n"
                                        f"You have {user_saves[0][0]} saves now.")

                if server_count % 100 == 0 and server_count % 1000 != 0:
                    db_update_saves = f"UPDATE {db_servers_table} SET Saves = Saves + 1 WHERE ServerID = {dc_id};"
                    db_cursor.execute(db_update_saves)
                    db_connection.commit()

                    db_check_saves = f"SELECT Saves FROM {db_servers_table} WHERE ServerID = %s;"
                    db_cursor.execute(db_check_saves, (dc_id,))
                    db_saves = db_cursor.fetchall()

                    await message.reply(f"{message.author.mention} great job, 1 Community Save was being added. 😍\n"
                                        f"In total we have {db_saves[0][0]} Community Saves now.")
                
                elif server_count % 1000 == 0:
                    db_update_saves = f"UPDATE {db_servers_table} SET Saves = Saves + 3 WHERE ServerID = %s;"
                    db_cursor.execute(db_update_saves, (dc_id,))
                    db_connection.commit()

                    db_check_saves = f"SELECT Saves FROM {db_servers_table} WHERE ServerID = %s;"
                    db_cursor.execute(db_check_saves, (dc_id,))
                    db_saves = db_cursor.fetchall()

                    await message.reply(f"{message.author.mention} wait, did we really reach {server_count}?\n"
                                        "Congratulations, 3 Community Saves were being added. 🤑\n"
                                        f"In total we have {db_saves[0][0]} Community Saves now.")

            elif message.author == self.last_author:
                await message.add_reaction("❌")
                
                db_check_saves = f"SELECT Saves FROM {db_servers_table} WHERE ServerID = %s;"
                db_cursor.execute(db_check_saves, (dc_id,))
                db_saves = db_cursor.fetchall()

                db_check_user_saves = f"SELECT saves FROM {db_users_table} WHERE user_id = aes_encrypt('{user_id}','{db_key}');"
                db_cursor.execute(db_check_user_saves)
                user_saves = db_cursor.fetchall()

                if int(user_saves[0][0]) > 0:

                    db_update_user_saves = f"UPDATE {db_users_table} SET saves = saves - 1 WHERE user_id = aes_encrypt('{user_id}','{db_key}');"
                    db_cursor.execute(db_update_user_saves)
                    db_connection.commit()

                    await message.reply(f"Are you in a hury {message.author.mention}? 😊\n"
                                    f"You have to wait for someone else to continue counting.\n"
                                    f"You have {user_saves[0][0]} User Saves left.\n"
                                    f"The next number is {self.expected_value}.")

                elif int(db_saves[0][0]) > 0:
                    db_update_saves = f"UPDATE {db_servers_table} SET Saves = Saves - 1 WHERE ServerID = %s;"
                    db_cursor.execute(db_update_saves, (dc_id,))
                    db_update_user_count = f"UPDATE {db_users_table} SET count = 0 WHERE user_id = aes_encrypt('{user_id}','{db_key}');"
                    db_cursor.execute(db_update_user_count)
                    db_connection.commit()

                    db_check_saves = f"SELECT Saves FROM {db_servers_table} WHERE ServerID = %s;"
                    db_cursor.execute(db_check_saves, (dc_id,))
                    db_saves = db_cursor.fetchall()

                    await message.reply(f"Are you in a hury {message.author.mention}? 😊\n"
                                    f"You have to wait for someone else to continue counting.\n"
                                    f"There are {db_saves[0][0]} left.\n"
                                    f"The next number is {self.expected_value}.")

                else:
                    db_update_user_count = f"UPDATE {db_users_table} SET count = 0 WHERE user_id = aes_encrypt('{user_id}','{db_key}');"
                    db_cursor.execute(db_update_user_count)
                    await message.reply(f"Are you in a hury {message.author.mention}? 😊\n"
                                        f"There are no community saves left but the count wont be reset.\n"
                                        f"But you have to be careful now!\n"
                                        f"The next number is {self.expected_value}.")

            else:
                await message.add_reaction("❌")
                db_check_saves = f"SELECT Saves FROM {db_servers_table} WHERE ServerID = %s;"
                db_cursor.execute(db_check_saves, (dc_id,))
                db_saves = db_cursor.fetchall()

                db_check_user_saves = f"SELECT saves FROM {db_users_table} WHERE user_id = aes_encrypt('{user_id}','{db_key}');"
                db_cursor.execute(db_check_user_saves)
                user_saves = db_cursor.fetchall()

                if int(user_saves[0][0]) > 0:

                    db_update_user_saves = f"UPDATE {db_users_table} SET saves = saves - 1 WHERE user_id = aes_encrypt('{user_id}','{db_key}');"
                    db_cursor.execute(db_update_user_saves)
                    db_connection.commit()

                    await message.reply(f"{message.author.mention} that's wrong. 💢\n"
                                        f"The next count is {self.expected_value}.\n"
                                        f"({user_saves[0][0]-1} User Saves left.)")

                elif int(db_saves[0][0]) > 0:
                    db_update_saves = f"UPDATE {db_servers_table} SET Saves = Saves - 1 WHERE ServerID = %s;"
                    db_cursor.execute(db_update_saves, (dc_id,))
                    db_update_user_count = f"UPDATE {db_users_table} SET count = 0 WHERE user_id = aes_encrypt('{user_id}','{db_key}');"
                    db_cursor.execute(db_update_user_count)
                    db_connection.commit()

                    db_check_saves = f"SELECT Saves FROM {db_servers_table} WHERE ServerID = %s;"
                    db_cursor.execute(db_check_saves, (dc_id,))
                    db_saves = db_cursor.fetchall()

                    await message.reply(f"{message.author.mention} that's wrong. 💢\n"
                                        f"You have no User Saves left."
                                        f"The next count is {self.expected_value}.\n"
                                        f"({db_saves[0][0]} Community Saves left.)")

                else:
                    self.expected_value = 1
                    db_update_server_count = f"UPDATE {db_servers_table} SET Count = %s WHERE ServerID = %s;"
                    db_cursor.execute(db_update_server_count, (self.expected_value, dc_id))
                    db_update_user_count = f"UPDATE {db_users_table} SET count = 0 WHERE user_id = aes_encrypt('{user_id}','{db_key}');"
                    db_cursor.execute(db_update_user_count)
                    db_connection.commit()

                    await message.reply(f"{message.author.mention} that's wrong. 😱\n"
                                        f"Since there are no Community Saves left,\n"
                                        f"the count continues with 1.")

            self.last_author = message.author

        except mysql.connector.Error as db_e:
            print(f"An database error occurred: {db_e}\n"
                   "Logging in again.")
            sql_logon()

        except Exception as e:
            print(f"An error occurred: {e}")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.channel.id != self.count_channel_id or after.author.bot:
            return

        await after.reply(f"{after.author.mention} edited the message. 🤔\n"
                          f"The next number is {self.expected_value}.")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.id != self.count_channel_id or message.author.bot:
            return

        await message.channel.send(f"{message.author.mention} deleted the message. 😮\n"
                                   f"The next number is {self.expected_value}.")


def setup(bot):
    bot.add_cog(COUNT(bot))
