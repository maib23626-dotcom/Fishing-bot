import discord
from discord.ext import commands
import random

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------------
# Cá theo độ hiếm
# -----------------------------
fish_data = {
    "Common": {
        "🐟 Cá chép": 600,
        "🐠 Cá rô phi": 400,
        "🐡 Cá trê": 500,
        "🐠 Cá basa": 550,
    },
    "Uncommon": {
        "🐟 Cá lóc": 700,
        "🐠 Cá chim trắng": 800,
        "🐟 Cá mè": 600,
        "🦐 Tôm": 2500,
    },
    "Rare": {
        "🐟 Cá hồi": 3500,
        "🦑 Mực": 2000,
        "🐟 Cá bống tượng": 1800,
    },
    "Epic": {
        "🐟 Cá tra dầu": 4000,
        "🐍 Cá chình": 5000,
        "🐠 Cá dìa": 2200,
        "🦪 Bào ngư": 6000,
    },
    "Legendary": {
        "🐟 Cá ngừ đại dương": 7000,
        "🐋 Cá nhám voi": 10000,
        "🐟 Cá nhụ": 4500,
        "🦪 Sò điệp lớn": 5500,
    },
    "Mythic": {
        "🦈 Cá mập": 15000,
        "🐢 Rùa Hoàn Kiếm": 50000,
        "💎 Ngọc trai quý": 30000,
    }
}

rarity_base_rates = {
    "Common": 60,
    "Uncommon": 20,
    "Rare": 10,
    "Epic": 5,
    "Legendary": 3,
    "Mythic": 2
}

# -----------------------------
# Shop items
# -----------------------------
shop_items = {
    "🎣 Cần tre": {"price": 0, "luck": 0, "durability": 50},
    "🎣 Cần sắt": {"price": 100000, "luck": 5, "durability": 100},
    "🎣 Cần vàng": {"price": 500000, "luck": 15, "durability": 200},
    "🎣 Cần kim cương": {"price": 2000000, "luck": 30, "durability": 500},
    "🪱 Mồi thường": {"price": 1000, "luck": 2, "durability": 20},
    "🪱 Mồi đặc biệt": {"price": 10000, "luck": 10, "durability": 50},
}

# -----------------------------
# Dữ liệu người chơi
# -----------------------------
inventories = {}   # {user_id: [(fish, weight, rarity), ...]}
balances = {}      # {user_id: money}
gears = {}         # {user_id: {"rod": {...}, "bait": {...}, "rod_dur": x, "bait_dur": y}}
fish_log = {}      # {user_id: {fish_name: {"rarity": str, "max_weight": float}}}

# -----------------------------
# Random trọng lượng
# -----------------------------
def random_weight(rarity):
    if rarity == "Common":
        return round(random.uniform(0.2, 3), 2)
    elif rarity == "Uncommon":
        return round(random.uniform(0.5, 4), 2)
    elif rarity == "Rare":
        return round(random.uniform(1, 6), 2)
    elif rarity == "Epic":
        return round(random.uniform(2, 10), 2)
    elif rarity == "Legendary":
        return round(random.uniform(5, 50), 2)
    elif rarity == "Mythic":
        return round(random.uniform(10, 200), 2)
    return 1.0

# -----------------------------
# Chọn cá theo rarity
# -----------------------------
def get_random_fish(user):
    # base
    rates = rarity_base_rates.copy()

    # bonus từ cần câu và mồi
    luck_bonus = 0
    if user in gears:
        rod = gears[user].get("rod")
        bait = gears[user].get("bait")
        if rod: luck_bonus += rod["luck"]
        if bait: luck_bonus += bait["luck"]

    # phân bổ luck cho rarities hiếm hơn
    rates["Rare"] += luck_bonus
    rates["Epic"] += luck_bonus // 2
    rates["Legendary"] += luck_bonus // 3
    rates["Mythic"] += luck_bonus // 5
    # giảm common tương ứng
    rates["Common"] = max(5, rates["Common"] - luck_bonus)

    # chọn rarity
    rarities, probs = zip(*rates.items())
    rarity = random.choices(rarities, weights=probs, k=1)[0]

    fish = random.choice(list(fish_data[rarity].keys()))
    price = fish_data[rarity][fish]
    weight = random_weight(rarity)
    return fish, weight, rarity, price

# -----------------------------
# Slash: câu cá
# -----------------------------
@bot.tree.command(name="cauca", description="Thả cần câu cá 🎣")
async def cauca(interaction: discord.Interaction):
    user = interaction.user.id

    # init gear nếu chưa có
    if user not in gears:
        gears[user] = {
            "rod": shop_items["🎣 Cần tre"].copy(),
            "bait": shop_items["🪱 Mồi thường"].copy(),
            "rod_dur": shop_items["🎣 Cần tre"]["durability"],
            "bait_dur": shop_items["🪱 Mồi thường"]["durability"]
        }

    if gears[user]["rod_dur"] <= 0:
        await interaction.response.send_message("❌ Cần câu của bạn đã hỏng, hãy mua cái mới trong /shop!")
        return
    if gears[user]["bait_dur"] <= 0:
        await interaction.response.send_message("❌ Hết mồi, hãy mua thêm trong /shop!")
        return

    gears[user]["rod_dur"] -= 1
    gears[user]["bait_dur"] -= 1

    caught = []
    for _ in range(random.randint(1, 3)):  # câu 1–3 con
        fish, weight, rarity, price = get_random_fish(user)
        inventories.setdefault(user, []).append((fish, weight, rarity))

        # update fish log
        fish_log.setdefault(user, {})
        if fish not in fish_log[user]:
            fish_log[user][fish] = {"rarity": rarity, "max_weight": weight}
        else:
            if weight > fish_log[user][fish]["max_weight"]:
                fish_log[user][fish]["max_weight"] = weight

        caught.append(f"{fish} — {rarity} — {weight}kg")

    result = "\n".join(caught)
    await interaction.response.send_message(
        f"{interaction.user.mention} 🎣 câu được:\n{result}\n"
        f"⚙️ Durability còn lại: Rod {gears[user]['rod_dur']} | Bait {gears[user]['bait_dur']}"
    )

# -----------------------------
# Slash: inventory
# -----------------------------
@bot.tree.command(name="inventory", description="Xem túi đồ 🎒")
async def inventory(interaction: discord.Interaction):
    user = interaction.user.id
    if user not in inventories or not inventories[user]:
        await interaction.response.send_message("🎒 Túi của bạn đang rỗng!")
        return

    items = "\n".join([f"{fish} ({w}kg, {r})" for fish, w, r in inventories[user]])
    bal = balances.get(user, 0)
    await interaction.response.send_message(
        f"🎒 Túi đồ của {interaction.user.mention}:\n{items}\n\n💰 Số dư: {bal:,} VNĐ"
    )

# -----------------------------
# Slash: bán cá
# -----------------------------
@bot.tree.command(name="ban", description="Bán toàn bộ cá trong túi")
async def ban(interaction: discord.Interaction):
    user = interaction.user.id
    if user not in inventories or not inventories[user]:
        await interaction.response.send_message("👜 Túi trống trơn!")
        return

    total = 0
    details = []
    for fish, weight, rarity in inventories[user]:
        price = fish_data[rarity][fish] * weight
        total += price
        details.append(f"{fish} ({weight}kg, {rarity}) = {round(price):,} VNĐ")

    inventories[user].clear()
    balances[user] = balances.get(user, 0) + total

    detail_msg = "\n".join(details)
    await interaction.response.send_message(
        f"💸 {interaction.user.mention} đã bán cá!\n{detail_msg}\n**Tổng cộng: {round(total):,} VNĐ**"
    )

# -----------------------------
# Slash: shop
# -----------------------------
@bot.tree.command(name="shop", description="Xem shop 🛒")
async def shop(interaction: discord.Interaction):
    items = "\n".join([f"{item} — {info['price']:,} VNĐ (Luck {info['luck']} | Durability {info['durability']})"
                       for item, info in shop_items.items()])
    await interaction.response.send_message(f"🛒 **Shop**:\n{items}\n\nDùng `/mua <tên>` để mua.")

# -----------------------------
# Slash: mua
# -----------------------------
@bot.tree.command(name="mua", description="Mua item từ shop")
async def mua(interaction: discord.Interaction, item: str):
    user = interaction.user.id
    if item not in shop_items:
        await interaction.response.send_message("❌ Item không tồn tại!")
        return

    price = shop_items[item]["price"]
    if balances.get(user, 0) < price:
        await interaction.response.send_message("❌ Không đủ tiền!")
        return

    balances[user] -= price
    if "Cần" in item:
        gears.setdefault(user, {})["rod"] = shop_items[item].copy()
        gears[user]["rod_dur"] = shop_items[item]["durability"]
    elif "Mồi" in item:
        gears.setdefault(user, {})["bait"] = shop_items[item].copy()
        gears[user]["bait_dur"] = shop_items[item]["durability"]

    await interaction.response.send_message(f"✅ {interaction.user.mention} đã mua {item} thành công!")

# -----------------------------
# Slash: leaderboard
# -----------------------------
@bot.tree.command(name="leaderboard", description="Xem bảng xếp hạng 💰")
async def leaderboard(interaction: discord.Interaction):
    if not balances:
        await interaction.response.send_message("📉 Chưa có ai bán cá!")
        return

    ranking = sorted(balances.items(), key=lambda x: x[1], reverse=True)
    top10 = ranking[:10]
    msg = []
    for i, (user_id, money) in enumerate(top10, start=1):
        user = await bot.fetch_user(user_id)
        msg.append(f"**{i}.** {user.name} — {money:,} VNĐ")

    leaderboard_text = "\n".join(msg)
    await interaction.response.send_message(
        f"🏆 **Bảng xếp hạng ngư ông giàu nhất** 🏆\n\n{leaderboard_text}"
    )

# -----------------------------
# Slash: fishdex / profile
# -----------------------------
@bot.tree.command(name="fishdex", description="Xem bộ sưu tập cá 📖")
async def fishdex(interaction: discord.Interaction):
    user = interaction.user.id
    if user not in fish_log or not fish_log[user]:
        await interaction.response.send_message("📖 Bạn chưa câu được con cá nào!")
        return

    records = []
    for fish, data in fish_log[user].items():
        records.append(f"{fish} — {data['rarity']} — Max: {data['max_weight']}kg")

    result = "\n".join(records)
    await interaction.response.send_message(
        f"📖 Hồ sơ câu cá của {interaction.user.mention}:\n{result}"
    )

# -----------------------------
# Ready event
# -----------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot đã đăng nhập thành {bot.user}")
import os
bot.run(os.getenv("DISCORD_TOKEN"))
