import os
import discord
from discord.ext import commands

# ============ الإعدادات الأساسية ============

TOKEN = os.getenv("DISCORD_TOKEN")  # التوكن غناخدوه من متغيّر بيئة
CREATE_CHANNEL_ID = 1444632951332671509


intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)

# نخزن مول كل روم مؤقت: {channel_id: owner_id}
room_owners: dict[int, int] = {}


# ============ لما البوت يشتغل ============

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (CheikhBot)")
    await bot.change_presence(
        activity=discord.Game(".v gouli | CheikhBot")
    )


# ============ helper: واش هاذ الروم من رومات البوت؟ ============

def is_temp_room(guild: discord.Guild, channel: discord.VoiceChannel | None) -> bool:
    """نحددو واش هاذ الروم وحدة من الرومات المؤقتة ديال البوت"""
    if channel is None:
        return False

    # إذا كانت مسجلة فـ room_owners → أكيد روم مؤقتة
    if channel.id in room_owners:
        return True

    creator = guild.get_channel(CREATE_CHANNEL_ID)
    if not isinstance(creator, discord.VoiceChannel):
        return False

    # نفس الكاتيجوري + ماشي قناة الإنشاء نفسها + الاسم يسالي بـ " Room"
    if (
        channel.id != CREATE_CHANNEL_ID
        and channel.category == creator.category
        and channel.name.endswith(" Room")
    ):
        return True

    return False


# ============ إنشاء / حذف الرومات المؤقتة ============

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # إنشاء روم جديد ملي يدخل العضو لقناة الإنشاء
    if after and after.channel and after.channel.id == CREATE_CHANNEL_ID and (
        not before or before.channel != after.channel
    ):
        category = after.channel.category

        try:
            new_channel = await guild.create_voice_channel(
                name=f"{member.name} Room",
                category=category
            )

            await member.move_to(new_channel)

            room_owners[new_channel.id] = member.id
            print(f"▶ Created room {new_channel.name} for {member}")
        except Exception as e:
            print(f"⚠️ Error while creating temp room: {e}")

    # حذف الروم المؤقت ملي يفرّغ
    if before and before.channel and is_temp_room(guild, before.channel):
        channel = before.channel
        if len(channel.members) == 0:
            name = channel.name
            room_owners.pop(channel.id, None)
            try:
                await channel.delete()
                print(f"🗑 Deleted empty room {name}")
            except discord.Forbidden:
                print(f"⚠️ ما قدرتش نمسح الروم {name} بسبب الصلاحيات.")
            except Exception as e:
                print(f"⚠️ خطأ غير متوقَّع ملي بغيت نمسح الروم {name}: {e}")


# ============ دالة: تأكد أنو مول الروم ============

def is_room_owner():
    async def predicate(ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.reply("❌ خصّك تكون فـ روم باش تگدر تگيس هاذ الأمر.")
            return False

        channel = ctx.author.voice.channel
        guild = ctx.guild

        # واش هاذ الروم من رومات البوت؟
        if not is_temp_room(guild, channel):
            await ctx.reply("❌ هاذ روم ماهي من الرومات اللي خالقهم CheikhBot.")
            return False

        owner_id = room_owners.get(channel.id)

        # لو ضاع المالك من الذاكرة، نخلي اللي كيهضر دابا مول جديد
        if owner_id is None:
            room_owners[channel.id] = ctx.author.id
            owner_id = ctx.author.id

        if owner_id != ctx.author.id:
            await ctx.reply("❌ غير مول روم يگد يدير هاذ الأمر.")
            return False

        return True

    return commands.check(predicate)


# ============ مجموعة أوامر .v ============

@bot.group(name="v", invoke_without_command=True)
async def v_group(ctx: commands.Context):
    """ .v gouli """
    txt = (
        "🧾 **أوامر فالرومات المؤقتة:**\n"
        "> `.v asm <اسم>` → تبدّل اسم روم\n"
        "> `.v tir @حد` → طيّر حد من روم وتمنعو يرجع\n"
        "> `.v majma3 <عدد>` → دير حدّ لأصحاب روم\n"
        "> `.v agfal` → گفّل روم\n"
        "> `.v afta7` → فتّح روم\n"
        "> `.v mar7ba @حد` → تسمح لحد يدخل روم\n"
        "> `.v mreg @حد` → تمنع حد يزيد يدخل روم\n"
        "> `.v 7os` → تحوص روم لي ما عندها مولاها\n"
        "> `.v 7awal @حد` → تحوّل روم لحد آخر\n"
        "> `.v mnasas @حد` → تبنِيه من روم\n"
        "> `.v lahisame7 @حد` → ترفع عليه البان\n"
        "> `.v gouli` → تعطيك معلومات عن روم\n"
        "> `.v moulchi` → تورّيك شكون مول روم\n"
        "> `.v i3dadat` → تورّيك الإعدادات ديال روم\n"
        "> `.v 3am` → تخلي روم عام\n"
        "> `.v khas` → تخليه خاص\n"
    )
    await ctx.reply(txt)


# ============ تغيير اسم روم → .v asm ============

@v_group.command(name="asm")
@is_room_owner()
async def v_asm(ctx: commands.Context, *, new_name: str):
    channel = ctx.author.voice.channel
    await channel.edit(name=new_name)
    await ctx.reply(f"✅ **تبدّل اسم روم إلى:** `{new_name}`")


# ============ طرد عضو من روم + منع الرجوع → .v tir ============

@v_group.command(name="tir")
@is_room_owner()
async def v_tir(ctx: commands.Context, member: discord.Member):
    channel = ctx.author.voice.channel

    if member not in channel.members:
        await ctx.reply("❌ هاذ الشخص ما هو فروم معاك.")
        return

    # طيّرو من الروم
    await member.move_to(None)

    # منعو من الرجوع للروم
    overwrites = channel.overwrites_for(member)
    overwrites.connect = False
    await channel.set_permissions(member, overwrite=overwrites)

    await ctx.reply(f"☑️ **طيّرت {member.mention} ومنعتو من الرجعة للروم.**")


# ============ تحديد عدد الأعضاء → .v majma3 ============

@v_group.command(name="majma3")
@is_room_owner()
async def v_majma3(ctx: commands.Context, limit: int):
    channel = ctx.author.voice.channel

    if limit < 0 or limit > 99:
        await ctx.reply("❌ عطيني عدد بين 0 و 99 .")
        return

    await channel.edit(user_limit=limit if limit > 0 else 0)
    await ctx.reply(f"📊 **الحد :** `{limit}`")


# ============ قفل روم → .v agfal ============

@v_group.command(name="agfal")
@is_room_owner()
async def v_agfal(ctx: commands.Context):
    channel = ctx.author.voice.channel

    # قفل الروم على الجميع
    overwrites = channel.overwrites_for(ctx.guild.default_role)
    overwrites.connect = False
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)

    # نخلي البوت ديما يقدر يدخل ويتحكم
    bot_overwrites = channel.overwrites_for(ctx.guild.me)
    bot_overwrites.connect = True
    bot_overwrites.manage_channels = True
    bot_overwrites.view_channel = True
    await channel.set_permissions(ctx.guild.me, overwrite=bot_overwrites)

    await ctx.reply("🔒 **گفلت روم….**")


# ============ فتح روم → .v afta7 ============

@v_group.command(name="afta7")
@is_room_owner()
async def v_afta7(ctx: commands.Context):
    channel = ctx.author.voice.channel
    overwrites = channel.overwrites_for(ctx.guild.default_role)
    overwrites.connect = None
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
    await ctx.reply("🔓 **فتّحت روم… .**")


# ============ permit → .v mar7ba ============

@v_group.command(name="mar7ba")
@is_room_owner()
async def v_mar7ba(ctx: commands.Context, member: discord.Member):
    channel = ctx.author.voice.channel
    overwrites = channel.overwrites_for(member)
    overwrites.connect = True
    await channel.set_permissions(member, overwrite=overwrites)
    await ctx.reply(f"🌿 **راهو مرحّب بـ {member.mention} فروم.**")


# ============ reject → .v mreg ============

@v_group.command(name="mreg")
@is_room_owner()
async def v_mreg(ctx: commands.Context, member: discord.Member):
    channel = ctx.author.voice.channel
    overwrites = channel.overwrites_for(member)
    overwrites.connect = False
    await channel.set_permissions(member, overwrite=overwrites)
    await ctx.reply(f"🚫 **{member.mention} مْرَگ من روم، ما عاد يدخل.**")


# ============ ban → .v mnasas ============

@v_group.command(name="mnasas")
@is_room_owner()
async def v_mnasas(ctx: commands.Context, member: discord.Member):
    channel = ctx.author.voice.channel
    overwrites = channel.overwrites_for(member)
    overwrites.connect = False
    await channel.set_permissions(member, overwrite=overwrites)
    await ctx.reply(f"⛔ **{member.mention} تبانا من الروم.**")


# ============ unban → .v lahisame7 ============

@v_group.command(name="lahisame7")
@is_room_owner()
async def v_lahisame7(ctx: commands.Context, member: discord.Member):
    channel = ctx.author.voice.channel
    overwrites = channel.overwrites_for(member)
    overwrites.connect = None
    await channel.set_permissions(member, overwrite=overwrites)
    await ctx.reply(f"✅ ** {member.mention}… يگد يرجع لروم.**")


# ============ claim → .v 7os ============

@v_group.command(name="7os")
async def v_7os(ctx: commands.Context):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.reply("❌ خصّك تكون فواحد روم باش تحوصو.")
        return

    channel = ctx.author.voice.channel
    guild = ctx.guild

    if not is_temp_room(guild, channel):
        await ctx.reply("❌ هاذ روم ماشي من الرومات اللي خالقهم CheikhBot.")
        return

    current_owner = room_owners.get(channel.id)
    if current_owner is not None and current_owner in [m.id for m in channel.members]:
        await ctx.reply("❌ مول روم راه ما زال فالروم، ما تگد تحوصو دابا.")
        return

    room_owners[channel.id] = ctx.author.id
    await ctx.reply("👑 **حصة روم… راه ولا لك انت.**")


# ============ transfer → .v 7awal @user ============

@v_group.command(name="7awal")
@is_room_owner()
async def v_7awal(ctx: commands.Context, member: discord.Member):
    channel = ctx.author.voice.channel
    if member not in channel.members:
        await ctx.reply("❌ خصّ الشخص جديد يكون فروم معاك.")
        return

    room_owners[channel.id] = member.id
    await ctx.reply(f"🤝 **حوّلت المْلك لـ {member.mention}، راه مول روم الجديد.**")


# ============ info → .v gouli ============

@v_group.command(name="gouli")
async def v_gouli(ctx: commands.Context):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.reply("❌ ما راك فحتى روم.")
        return

    channel = ctx.author.voice.channel
    guild = ctx.guild

    if not is_temp_room(guild, channel):
        await ctx.reply("❌ هاذ روم ماشي من رومات CheikhBot.")
        return

    owner_id = room_owners.get(channel.id)
    owner_mention = f"<@{owner_id}>" if owner_id else "ما عندو مول محدد"

    locked = "مفتوح"
    overwrites = channel.overwrites_for(ctx.guild.default_role)
    if overwrites.connect is False:
        locked = "مگفول"

    txt = (
        f"🧾 **معلومات عن روم:**\n"
        f"- الاسم: `{channel.name}`\n"
        f"- مولشي: {owner_mention}\n"
        f"- الحالة: {locked}\n"
        f"- الحد: `{channel.user_limit or 'ما كاين حد'}`\n"
    )
    await ctx.reply(txt)


# ============ owner → .v moulchi ============

@v_group.command(name="moulchi")
async def v_moulchi(ctx: commands.Context):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.reply("❌ ما راك فحتى روم.")
        return

    channel = ctx.author.voice.channel
    guild = ctx.guild

    if not is_temp_room(guild, channel):
        await ctx.reply("❌ هاذ روم ماشي من رومات CheikhBot.")
        return

    owner_id = room_owners.get(channel.id)

    if not owner_id:
        await ctx.reply("❌ هاذ روم ما عندو مول مسجّل عند CheikhBot.")
        return

    await ctx.reply(f"👑 **مول روم هو:** <@{owner_id}>")


# ============ settings → .v i3dadat ============

@v_group.command(name="i3dadat")
async def v_i3dadat(ctx: commands.Context):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.reply("❌ خصّك تكون فروم باش نشوف الإعدادات.")
        return

    channel = ctx.author.voice.channel
    guild = ctx.guild

    if not is_temp_room(guild, channel):
        await ctx.reply("❌ هاذ روم ماشي من رومات CheikhBot.")
        return

    overwrites = channel.overwrites_for(ctx.guild.default_role)
    locked = "مفتوح"
    if overwrites.connect is False:
        locked = "مگفول"

    txt = (
        f"⚙️ **إعدادات روم:**\n"
        f"- الاسم: `{channel.name}`\n"
        f"- الحالة: {locked}\n"
        f"- الحد: `{channel.user_limit or 'ما كاين حد'}`\n"
        f"- الكاتيجوري: `{channel.category.name if channel.category else 'ما عندو كاتيجوري'}`\n"
    )
    await ctx.reply(txt)


# ============ public → .v 3am ============

@v_group.command(name="3am")
@is_room_owner()
async def v_3am(ctx: commands.Context):
    channel = ctx.author.voice.channel
    overwrites = channel.overwrites_for(ctx.guild.default_role)
    overwrites.connect = None
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
    await ctx.reply("🌍 **روم ولا عام… أي حد يگد يدخل.**")


# ============ private → .v khas ============

@v_group.command(name="khas")
@is_room_owner()
async def v_khas(ctx: commands.Context):
    channel = ctx.author.voice.channel

    # منع الجميع من الدخول
    overwrites = channel.overwrites_for(ctx.guild.default_role)
    overwrites.connect = False
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)

    # خلي البوت ديما يقدر يدخل ويتحكم
    bot_overwrites = channel.overwrites_for(ctx.guild.me)
    bot_overwrites.connect = True
    bot_overwrites.manage_channels = True
    bot_overwrites.view_channel = True
    await channel.set_permissions(ctx.guild.me, overwrite=bot_overwrites)

    await ctx.reply("🔐 **روم ولا خاص… غير اللي تسمحلهم.**")


# ============ تشغيل البوت ============

bot.run(TOKEN)
