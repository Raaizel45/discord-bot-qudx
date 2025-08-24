import os
import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio

# Pobierz token ze zmiennych środowiskowych
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# :pushpin: Główny panel ticketów
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Partnerstwo", style=discord.ButtonStyle.primary, custom_id="ticket_partner", emoji="💼"))
        self.add_item(Button(label="Kontakt z administracją", style=discord.ButtonStyle.success, custom_id="ticket_admin", emoji="📞"))
        self.add_item(Button(label="Nagrody za zadania", style=discord.ButtonStyle.secondary, custom_id="ticket_rewards", emoji="📃"))
        self.add_item(Button(label="Inne", style=discord.ButtonStyle.danger, custom_id="ticket_other", emoji="❗"))


# :pushpin: Panel wewnątrz ticketa (przycisk zamykania)
class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(
            label="🔒 Zamknij ticket",
            style=discord.ButtonStyle.danger,
            custom_id="ticket_close"
        ))


@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")


# :pushpin: Obsługa interakcji (kliknięcia przycisków)
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.data.get("custom_id"):
        return

    guild = interaction.guild
    user = interaction.user
    custom_id = interaction.data["custom_id"]

    # --- Zamykanie ticketu ---
    if custom_id == "ticket_close":
        if interaction.channel.name.startswith("ticket-"):
            await interaction.response.send_message("🔒 Ticket zostanie zamknięty za 5 sekund...", ephemeral=True)
            await asyncio.sleep(5)
            await interaction.channel.delete()
        return

    # --- Tworzenie ticketu ---
    # Mapowanie przycisków na kategorie
    categories_map = {
        "ticket_partner": "🎫 Partnerstwo",
        "ticket_admin": "☎️ Administracja",
        "ticket_rewards": "🏆 Nagrody",
        "ticket_other": "❗ Inne"
    }

    # Wybieramy kategorię na podstawie przycisku
    category_name = categories_map.get(custom_id, "🎫 TICKETY")
    category = discord.utils.get(guild.categories, name=category_name)
    if category is None:
        category = await guild.create_category(category_name)

    # Sprawdzamy czy użytkownik już ma ticket w tej kategorii
    channel_name = f"ticket-{user.name}".replace(" ", "-").lower()
    existing = discord.utils.get(category.text_channels, name=channel_name)
    if existing:
        await interaction.response.send_message(f"❌ Masz już otwarty ticket: {existing.mention}", ephemeral=True)
        return

    # Uprawnienia do ticketa
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }

    # Dodajemy rolę administracji (ZMIEN nazwe roli na swoją!)
    admin_role = discord.utils.get(guild.roles, name="Admin")
    if admin_role:
        overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    # Tworzymy kanał w odpowiedniej kategorii
    channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)

    # Wiadomość powitalna w zależności od rodzaju ticketa
    if custom_id == "ticket_partner":
        msg = "💼 Witaj w tickecie **partnerstwa**! Opisz swoją propozycję."
    elif custom_id == "ticket_admin":
        msg = "📞 Witaj w tickecie **kontakt z administracją**! Opisz swój problem."
    elif custom_id == "ticket_rewards":
        msg = "📃 Witaj w tickecie **nagrody za zadania**! Podaj szczegóły."
    else:
        msg = "❗ Witaj w tickecie! Opisz swój problem."

    await channel.send(f"{user.mention} {msg}", view=CloseView())
    await interaction.response.send_message(f"✅ Ticket został utworzony: {channel.mention}", ephemeral=True)


# :pushpin: Komenda do wysłania panelu na kanał
@bot.command()
async def panel(ctx, channel: discord.TextChannel = None):
    """Wysyła panel ticketów"""
    view = TicketView()
    if channel is None:
        channel = ctx.channel

    await channel.send(
        ":ticket: **System ticketów**\n\n"
        "Wybierz rodzaj ticketa, który chcesz otworzyć:",
        view=view
    )
    await ctx.send(f"✅ Panel wysłany na {channel.mention}", delete_after=5)


# :rocket: URUCHOMIENIE BOTA
if __name__ == "__main__":
    bot.run(TOKEN)
