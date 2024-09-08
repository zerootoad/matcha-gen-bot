import json, os, discord
from discord.ext import commands

class ExtraUtilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        current_dir = os.path.dirname(__file__)
        bot_dir = os.path.dirname(current_dir)

        self.cfgs_folder = os.path.join(bot_dir, 'assets', 'cfgs')
        self.log_file = os.path.join(bot_dir, 'assets', 'generation_logs.json')
        self.feedbacks_file = os.path.join(bot_dir, 'assets', 'feedbacks.json')

        if not os.path.exists(self.cfgs_folder):
            os.makedirs(self.cfgs_folder)

    @commands.slash_command(name="information", description="View generation or feedback statistics.")
    @discord.option("about", str, description="Choose what you wanna view information about.", choices=["Generation", "Feedback", "Both"])
    async def information(self, interaction, about: str = "Both"):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(title="`❌` **Not Eligible**", description=f"You do not have access to use this command.", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed, ephemeral=True)
            return

        with open(self.feedbacks_file, 'r+') as f:
            feedback_data = json.load(f) 
        
        with open(self.log_file, 'r+') as f:
            log_data = json.load(f)
        
        if not feedback_data and not log_data:
            embed = discord.Embed(title="`❌` **No Data Available**", description="No generation or feedback data found.", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed, ephemeral=True)
            return

        total_generations = 0
        total_paid_generations = 0
        total_free_generations = 0
        ai_generations = 0
        math_generations = 0
        total_feedbacks = 0
        paid_feedbacks = 0
        free_feedbacks = 0
        ai_feedbacks = 0
        math_feedbacks = 0

        generation_summary = ""

        if about in ["Both", "Generation"]:
            total_generations = log_data.get("paid", 0) + log_data.get("free", 0)
            total_paid_generations = log_data.get("paid", 0)
            total_free_generations = log_data.get("free", 0)
            ai_generations = log_data.get("ai", 0)
            math_generations = log_data.get("math", 0)

        if about in ["Both", "Feedback"]:
            for config_name, feedbacks in feedback_data.items():
                is_ai = "ai" in config_name.lower()[:2]
                is_paid = "paid" in config_name.lower()

                num_feedbacks = len(feedbacks)
                total_feedbacks += num_feedbacks

                if is_paid:
                    paid_feedbacks += num_feedbacks
                else:
                    free_feedbacks += num_feedbacks       
                    
                if is_ai:
                    ai_feedbacks += num_feedbacks
                else:
                    math_feedbacks += num_feedbacks         

                generation_summary += f"**{config_name}:**\n"
                generation_summary += f"> Number of Feedbacks: {num_feedbacks}\n"
                generation_summary += f"> Type: {'AI' if is_ai else 'Math'}\n"
                generation_summary += f"> {'Paid' if is_paid else 'Free'} Generation\n\n"
            
        if about == "Generation":
            embed = discord.Embed(title=f"`📊` **Generation Statistics**", color=0x88CFF8)
            embed.add_field(name="Total Generations", value=f"{total_generations}", inline=False)
            embed.add_field(name=f"Paid Generations: {total_paid_generations}", value=f"> AI Generations: {ai_generations}\n> Math Generations: {math_generations}", inline=False)
            embed.add_field(name=f"Free Generations", value=f"{total_free_generations}", inline=True)
            
            await interaction.respond(embed=embed)
            await interaction.followup.send(file=discord.File(self.log_file, f"generation_logs.json"), ephemeral=True)
        
        elif about == "Feedback":
            embed = discord.Embed(title=f"`📊` **Feedback Statistics**", color=0x88CFF8)
            embed.add_field(name="Total Feedbacks", value=f"{total_feedbacks}", inline=False)
            embed.add_field(name=f"Paid Feedbacks: {paid_feedbacks}", value=f"> AI Feedbacks: {ai_feedbacks}\n> Math Feedbacks: {math_feedbacks}", inline=False)
            embed.add_field(name="Free Feedbacks", value=f"{free_feedbacks}", inline=True)
            
            await interaction.respond(embed=embed)
            if generation_summary:
                await interaction.followup.send("Detailed information on generations:\n" + generation_summary, ephemeral=True)
            await interaction.followup.send(file=discord.File(self.feedbacks_file, f"feedbacks.json"), ephemeral=True)

        else:
            embed1 = discord.Embed(title=f"`📊` **Generation Statistics**", color=0x88CFF8)
            embed1.add_field(name="Total Generations", value=f"{total_generations}", inline=False)
            embed1.add_field(name=f"Paid Generations: {total_paid_generations}", value=f"> AI Generations: {ai_generations}\n> Math Generations: {math_generations}", inline=False)
            embed1.add_field(name=f"Free Generations", value=f"{total_free_generations}", inline=True)
            
            embed2 = discord.Embed(title=f"`📊` **Feedback Statistics**‎ ‎ ‎ ", color=0x88CFF8)
            embed2.add_field(name="Total Feedbacks", value=f"{total_feedbacks}", inline=False)
            embed2.add_field(name=f"Paid Feedbacks: {paid_feedbacks}", value=f"> AI Feedbacks: {ai_feedbacks}\n> Math Feedbacks: {math_feedbacks}", inline=False)
            embed2.add_field(name="Free Feedbacks", value=f"{free_feedbacks}", inline=True)
            
            await interaction.respond(embeds=[embed1, embed2])
            if generation_summary:
                await interaction.followup.send("Detailed information on generations:\n" + generation_summary, ephemeral=True)
            await interaction.followup.send(file=discord.File(self.log_file, "generation_logs.json"), ephemeral=True)
            await interaction.followup.send(file=discord.File(self.feedbacks_file, "feedbacks.json"), ephemeral=True)
            
            
    @discord.slash_command(name="upload", description="Upload your configuration as .cfg template!")
    @discord.option("file", discord.Attachment, description="Attach your .cfg file here. Drag-n-Drop or browse and pick for the .cfg file.")
    async def upload(self, interaction, file: discord.Attachment):
        if not file.filename.endswith(".cfg"):
            embed = discord.Embed(title="`❌` **Invalid Format**", description=f"Make sure to upload a .cfg file", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed)
            return
        
        try:
            config_content = await file.read()
            config_data = json.loads(config_content)

            if 'prediction_x' not in config_data:
                raise KeyError("Missing 'skeleton' key")
        
        except json.JSONDecodeError:
            embed = discord.Embed(title="`❌` **Invalid Content**", description=f"Failed to parse the .cfg file. Ensure it's a valid JSON.", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed)
            return
        except KeyError:
            embed = discord.Embed(title="`❌` **Invalid Content**", description=f"Make sure the .cfg file includes all necessary fields.", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed)
            return
        
        file_path = os.path.join(self.cfgs_folder, f"{interaction.user.id}.cfg")        
        with open(file_path, 'wb') as f:
            f.write(config_content)
        
        embed = discord.Embed(title="`🎀` **Upload Successful**", description=f"Your configuration template has been uploaded successfully!", color=0xFF88CF)
        embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
        await interaction.respond(embed=embed)
        
    

def setup(bot):
    bot.add_cog(ExtraUtilities(bot))
