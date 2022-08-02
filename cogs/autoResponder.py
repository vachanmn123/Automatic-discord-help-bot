import disnake
from disnake.ext import commands
from fuzzywuzzy import process, fuzz
import os
import json


class AutoResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        resp = await self.get_response(message.content.lower())
        if resp is not None:
            emb = disnake.Embed(title=resp["name"], description=resp["description"])
            emb.set_author(name=resp["author"])
            emb.add_field(name="Most Probable Solution", value=resp["response"])
            if len(resp["media_links"]) > 0:
                await message.reply(embed=emb)
                return await message.channel.send("\n".join(resp["media_links"]))
            return await message.reply(embed=emb)

    async def get_response(self, message: str):
        """get the right response from the files

        Args:
            message (str): the message to get the response for

        Returns:
            dict: the response file
        """
        # Initialize a variable to store the best response
        highest_fuzzy_match = (0, "")
        for response_file in os.listdir("responses"):
            # check every file in the responses/ folder, if it isnt a json file, skip it
            if not response_file.endswith(".json"):
                continue
            keywords = json.load(open(f"responses/{response_file}"))["keywords"]
            for keyword in keywords:
                # check if the keyword is in the message, if the search has a fuzzy_ratio of more than 80, save it.
                fuzz_ratio = fuzz.ratio(message, keyword.lower())
                self.bot.logger.debug(
                    f"Checking {keyword} against {message}. Fuzzy match: {fuzz_ratio}"
                )
                if fuzz_ratio > highest_fuzzy_match[0] and fuzz_ratio >= 80:
                    highest_fuzzy_match = (fuzz_ratio, response_file)
        if highest_fuzzy_match[0] == 0:
            # If no match was found, return None
            return None
        # If match was found, return the response file
        return json.load(open(f"responses/{highest_fuzzy_match[1]}"))


def setup(bot):
    bot.add_cog(AutoResponder(bot))
    bot.logger.info("AutoResponder loaded")
    return bot
