import os, discord, re, json
from discord.ext import commands
from typing import Optional
from handlers.paid.generator import PaidGenHandler
from handlers.free.generator import FreeGenHandler
from handlers.config_handler import ConfigHandler
from discord.ui import Modal, View, InputText, Button
from discord import Interaction, InputTextStyle, ButtonStyle

class FeedbackModal(Modal):
    def __init__(self, config_name: str, ping: int, ai: bool, user_id: int):
        super().__init__(title="Provide Feedback")
        
        self.config_name = config_name
        self.ping = ping
        self.ai = ai
        self.user_id = user_id
    
        current_dir = os.path.dirname(__file__)
        bot_dir = os.path.dirname(current_dir)
        
        self.feedbacks_file = os.path.join(bot_dir, 'assets', 'feedbacks.json')

        self.add_item(InputText(
            label="Your Feedback",
            style=InputTextStyle.paragraph,
            placeholder="Please provide your feedback here...",
            required=True,
            max_length=1000
        ))

    async def callback(self, interaction: Interaction):
        feedback_data = {
            "user_id": self.user_id,
            "ping": self.ping,
            "ai": self.ai,
            "feedback": self.children[0].value 
        }
        self._log_feedback(feedback_data)
                
        await interaction.response.send_message("Thank you for your feedback! It will be used to improve our generator.", ephemeral=True)
        
        message = await interaction.channel.fetch_message(interaction.message.id)
        view = View.from_message(message)

        for item in view.children:
            if isinstance(item, Button):
                item.disabled = True
                
        await interaction.message.edit(view=view)

    def _log_feedback(self, feedback):
        try:
            if os.path.exists(self.feedbacks_file):
                with open(self.feedbacks_file, 'r') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = {}
            else:
                data = {}

            if self.config_name not in data:
                data[self.config_name] = []

            data[self.config_name].append(feedback)
            with open(self.feedbacks_file, 'w') as f:
                json.dump(data, f, indent=4)

        except Exception as e:
            print(f"Error logging feedback: {str(e)}")




class FeedbackView(View):
    def __init__(self, config_name: str, ping: int, ai: bool, user_id: int):
        super().__init__()
        self.config_name = config_name
        self.ping = ping
        self.ai = ai
        self.user_id = user_id

    @discord.ui.button(label="Provide Feedback", style=ButtonStyle.success, emoji="📝")
    async def feedback_button(self, button: Button, interaction: Interaction):        
        await interaction.response.send_modal(FeedbackModal(self.config_name, self.ping, self.ai, self.user_id))

class ApiUtilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.paid = PaidGenHandler()
        self.free = FreeGenHandler()
        self.config = ConfigHandler()
        
        current_dir = os.path.dirname(__file__)
        bot_dir = os.path.dirname(current_dir)
        
        self.log_file = os.path.join(bot_dir, 'assets', 'generation_logs.json')
        self.cfgs_dir = os.path.join(bot_dir, 'assets', 'cfgs')
    
    def log_config(self, config_type: str, is_ai: bool):
        try:
            default_data = {
                "paid": 0,
                "free": 0,
                "ai": 0,
                "math": 0
            }

            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = default_data
            else:
                data = default_data

            if config_type == 'paid':
                data['paid'] += 1
            else:
                data['free'] += 1

            if is_ai:
                data['ai'] += 1
            else:
                data['math'] += 1

            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=4)

        except Exception as e:
            print(f"Error logging config: {str(e)}")

    
    @discord.slash_command(name="paid-config", description="Generate a paid configuration for Matcha!")
    @discord.option("config_name", str, description="Enter your custom config name. (Optional)")
    @discord.option("ping", int, description="Enter your in-game ping here.")
    @discord.option("ping_range", str, description="Enter a ping range. You must separate them with |, -, or ,.")
    @discord.option("mode", str, description="Enter your preferred mode. (Default: Blatant)", choices=["Blatant", "SemiLegit", "Legit", "Streamable"])
    @discord.option("ai", bool, description="Set to true if you would like to use the new AI feature. (Default: False)")
    @discord.option("model", str, description="Choose your preferred ai model. (Default: Stable)", choices=["Pre-Relase", "Stable"])
    async def paid_config(self, interaction, config_name: Optional[str] = None, ping: Optional[int] = None, ping_range: Optional[str] = None, mode: str = "None", ai: Optional[bool] = False, model: str = "Stable"):

        
        if interaction.guild.get_role(1278945247325327424) not in interaction.user.roles:
            embed = discord.Embed(title="`❌` **Not Eligible**", description=f"You do not have access to use the paid generator, please use `/free-config` instead.", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed, ephemeral=True)
            return     
        
        if ping and ping_range:
            embed = discord.Embed(title="`❌` **Invalid Format**", description=f"You have selected both \"ping-range\" and \"ping\" options, please select only one", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed, ephemeral=True)
            return
            
        if interaction.channel.id != 1278947864390799405:
            embed = discord.Embed(title="`❌` **Invalid Channel**", description=f"We've detected the bot being used in a wrong channel! Please only use the generator in <#1280371830489747519>", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed, ephemeral=True)
            return
        
        if ping is None and ping_range is None:
            embed = discord.Embed(title="`❌` **Missing Ping**", description=f"You must enter a ping value or range to get your configs!", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed, ephemeral=True)
            return
        
        if not ai and ping and (ping < 10 or ping > 200) or ping == 0:
            embed = discord.Embed(title="`❌` **Unsupported Ping**", description=f"Our maths option only supports ping through `10 - 200`. We will add more flexibility in v2...", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed, ephemeral=True)
            return
        
        elif ai and ping and (ping < 1 or ping > 1000) or ping == 0:
            embed = discord.Embed(title="`❌` **Unsupported Ping**", description=f"Please enter a valid **playable** ping", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed, ephemeral=True)
            return
        
        sens = 1
        smooth = 0
        if mode == "Blatant":
            smooth = 0
            sens = 1
        elif mode == "SemiLegit":
            smooth = 3
            sens = 0.70
        elif mode == "Legit":
            smooth = 7
            sens = 0.40
        else:
            smooth = 13
            sens = 0.20
                
        if ping_range:
            try:
                ping_min, ping_max = map(int, re.split(r'[|,\-]', ping_range))
            except ValueError:
                embed = discord.Embed(title="`❌` **Invalid Ping Range**", description="Please enter a valid ping range separated by |, -, or ,.", color=0xFF474C)
                embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                await interaction.respond(embed=embed, ephemeral=True)
                return
            
            if ping_min < 1 or ping_max > 1000 or ping_min == 0:
                embed = discord.Embed(title="`❌` **Invalid Ping Range**", description="Please enter a valid **playable** ping range.", color=0xFF474C)
                embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                await interaction.respond(embed=embed, ephemeral=True)
                return
            
            best_ping = (ping_min + ping_max) / 2

            try:
                xy_dict = self.paid.calculate(best_ping, model, ai)
            except Exception as e:
                embed = discord.Embed(title="`❌` **Unexpected Error**", description=f"Bot has run into an exception when generating configs, send the error message below to one of the developers\n> ```{e}```", color=0xFF474C)
                embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                await interaction.respond(embed=embed, ephemeral=True)
                return
            
            if "error" in xy_dict:
                embed = discord.Embed(title="`❌` **Unexpected Error**", description=f"Bot has run into an exception when generating configs, send the error message below to one of the developers\n> ```{xy_dict['error']}```", color=0xFF474C)
                embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                await interaction.respond(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(title="`⌛` **Sending User Config**", description=f"Please stay patient as the bot is sending your configuration...", color=0xFF88CF)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            message = await interaction.respond(embed=embed)
            
            file_path = self.config.generate_cfg_file(f"{'ai' if ai else 'math'}_paid_{mode.lower()}_{ping_min}-{ping_max}ping", xy_dict['x'], xy_dict['y'], smooth, sens)
            try:
                view = FeedbackView(f"{'ai' if ai else 'math'}_paid_{mode.lower()}_{ping_min}-{ping_max}ping", best_ping, ai, interaction.user.id)
                
                file_name = f"{'ai' if ai else 'math'}_paid_{mode.lower()}_{ping_min}-{ping_max}ping.cfg" if config_name is None else f"{config_name.lower()}.cfg"
                with open(file_path, 'rb') as file:
                    embed = discord.Embed(title="`🎀` **User Configuration**", description=f"Here's your **{mode.lower()}** generated configuration for **{ping_min}-{ping_max}** ping range", color=0xFF88CF)
                    embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                    await interaction.user.send(embed=embed, file=discord.File(file, file_name), view=view)
            except Exception as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                embed = discord.Embed(title="`❌` **Unexpected Error**", description=f"Our bot has failed to dm you your configuration. Please ensure that your dms are enabled, if so send the error message below to one of the developers\n> ```{e}```", color=0xFF474C)
                embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                await message.edit(embed=embed)
                return
            else:                    
                embed = discord.Embed(title="`🎀` **Config Sent**", description=f"Your configuration has been sent in our DMs!", color=0xFF88CF)
                embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                await message.edit(embed=embed)
        else:
            try:
                xy_dict = self.paid.calculate(ping, model, ai)
            except Exception as e:
                embed = discord.Embed(title="`❌` **Unexpected Error**", description=f"Bot has run into an exception when generating configs, send the error message below to one of the developers\n> ```{e}```", color=0xFF474C)
                embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                await interaction.respond(embed=embed, ephemeral=True)
                return
            
            if "error" in xy_dict:
                embed = discord.Embed(title="`❌` **Unexpected Error**", description=f"Bot has run into an exception when generating configs, send the error message below to one of the developers\n> ```{xy_dict['error']}```", color=0xFF474C)
                embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                await interaction.respond(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(title="`⌛` **Sending User Config**", description=f"Please stay patient as the bot is sending your configuration...", color=0xFF88CF)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            message = await interaction.respond(embed=embed)
            
            file_path = self.config.generate_cfg_file(f"{'ai' if ai else 'math'}_paid_{mode.lower()}_{ping}ping", xy_dict['x'], xy_dict['y'], smooth, sens)
            
            try:
                view = FeedbackView(f"{'ai' if ai else 'math'}_paid_{mode.lower()}_{ping}ping", ping, ai, interaction.user.id)
                
                file_name = f"{'ai' if ai else 'math'}_paid_{mode.lower()}_{ping}ping.cfg" if config_name is None else f"{config_name.lower()}.cfg"
                with open(file_path, 'rb') as file:
                    embed = discord.Embed(title="`🎀` **User Configuration**", description=f"Here's your **{mode.lower()}** generated configuration for **{ping}** ping", color=0xFF88CF)
                    embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                    await interaction.user.send(embed=embed, file=discord.File(file, file_name), view=view)
            except Exception as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
                embed = discord.Embed(title="`❌` **Unexpected Error**", description=f"Our bot has failed to dm you your configuration. Please ensure that your dms are enabled, if so send the error message below to one of the developers\n> ```{e}```", color=0xFF474C)
                embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                await message.edit(embed=embed)
                return
            else:                    
                embed = discord.Embed(title="`🎀` **Config Sent**", description=f"Your configuration has been sent in our DMs!", color=0xFF88CF)
                embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                await message.edit(embed=embed)
                
        template_path = os.path.join(self.cfgs_dir, f'{interaction.user.id}.cfg')
        if not os.path.exists(template_path):
            embed = discord.Embed(title="`❓` **Missing Template**", description=f"It seems like you're missing your config template file in our database, make sure to use `/upload [file]`. We will use the default template for this generation!", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.followup.send(embed=embed, ephemeral=True)                
          
        self.log_config("paid", ai)
                
                
    @discord.slash_command(name="free-config", description="Generate a free configuration for Matcha!")
    @discord.option("ping", int, description="Enter your in-game ping here.")
    @discord.option("mode", str, description="Enter your preferred mode. (Default: Blatant)", choices=["Blatant", "SemiLegit", "Legit", "Streamable"])
    async def free_config(self, interaction, ping: int, mode: str = "Blatant"):

        
        if interaction.channel.id != 1278947864390799405:
            embed = discord.Embed(title="`❌` **Invalid Channel**", description=f"We've detected the bot being used in a wrong channel! Please only use the generator in <#1280371830489747519>", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed, ephemeral=True)
            return
        
        if ping and (ping < 10 or ping > 200) or ping == 0:
            embed = discord.Embed(title="`❌` **Unsupported Ping**", description=f"Our maths option only supports ping through `10 - 200`. We will add more flexibility in v2...", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed, ephemeral=True)
            return
        
        sens = 1
        smooth = 0
        if mode == "Blatant":
            smooth = 0
            sens = 1
        elif mode == "SemiLegit":
            smooth = 3
            sens = 0.70
        elif mode == "Legit":
            smooth = 7
            sens = 0.40
        else:
            smooth = 13
            sens = 0.20
        
                
        try:
            xy_dict = self.free.calculate(ping)
        except Exception as e:
            embed = discord.Embed(title="`❌` **Unexpected Error**", description=f"Bot has run into an exception when generating configs, send the error message below to one of the developers\n> ```{e}```", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.respond(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(title="`⌛` **Sending User Config**", description=f"Please stay patient as the bot is sending your configuration...", color=0xFF88CF)
        embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
        message = await interaction.respond(embed=embed)
        
        file_path = self.config.generate_cfg_file(f"free_{mode.lower()}_{ping}ping", xy_dict['x'], xy_dict['y'], smooth, sens)
        try:
            view = FeedbackView(f"free_{mode.lower()}_{ping}ping", ping, False, interaction.user.id)
            
            with open(file_path, 'rb') as file:
                embed = discord.Embed(title="`🎀` **User Configuration**", description=f"Here's your **{mode.lower()}** generated configuration for **{ping}** ping", color=0xFF88CF)
                embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
                await interaction.user.send(embed=embed, file=discord.File(file, f"free_{mode.lower()}_{ping}ping.cfg"), view=view)
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)

            embed = discord.Embed(title="`❌` **Unexpected Error**", description=f"Our bot has failed to dm you your configuration. Please ensure that your dms are enabled, if so send the error message below to one of the developers\n> ```{e}```", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await message.edit(embed=embed)
            return
        finally:
            embed = discord.Embed(title="`🎀` **Config Sent**", description=f"Your configuration has been sent in our DMs!", color=0xFF88CF)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await message.edit(embed=embed)

        template_path = os.path.join(self.cfgs_dir, f'{interaction.user.id}.cfg')
        if not os.path.exists(template_path):
            embed = discord.Embed(title="`❓` **Missing Template**", description=f"It seems like you're missing your config template file in our database, make sure to use `/upload [file]`. We will use the default template for this generation!", color=0xFF474C)
            embed.set_footer(icon_url="https://i.ibb.co/JnnDpM5/9aa62f3dcfaa4fab6c445d846bb13a6c.webp", text=interaction.user.display_name)
            await interaction.followup.send(embed=embed, ephemeral=True)

        self.log_config("free", False)
                
                
def setup(bot):
    bot.add_cog(ApiUtilities(bot))
