# OrzMC 插件权限/指令清单（按插件分组）

> 生成时间：2026-08-30 17:12
> 生成方式：`scripts/plugin_inventory.py`（自动提取 jar plugin.yml + 人工补充字典 EXTRA_PERMS）
> 数据源：`/Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/716c2fb712154c36ba5ab0f1480d3f87/plugins/*.jar`（Paper 实例；2026-09-03 迁 MCSM 后）；组分配标注来源 `permission-groups.md` 唯一事实源
> 定时更新：重新运行 `python3 ~/.hermes/skills/gaming/orzmc/scripts/plugin_inventory.py` 即可（可挂 cron）

## 插件总览

| 插件 | 版本 | 指令数 | 权限数 | 角色 |
|:--|:--|--:|--:|:--|
| BackOnDeath | 0.4 | 1 | 2 | 死亡回点 |
| Essentials | 2.22.0 | 153 | 453 | 基础命令 |
| EzShops | 2.5.9 | 15 | 26 | 商店经济 |
| F3F4Perms | 1.3.0 | 2 | 4 | 游戏模式热键 |
| GetMeHome | 3.0.0 | 6 | 14 | 家传送 |
| Geyser-Spigot | 2.11.2-SNAPSHOT | 1 | 1 | 基岩互通 |
| GriefPrevention | 16.18.7 | 46 | 37 | 领地/圈地 |
| LoginSecurity | 3.3.2-SNAPSHOT | 6 | 2 | 登录保护 |
| LuckPerms | 5.5.81 | 2 | 4 | 权限管理 |
| OrzMC | 1.0.24 | 5 | 4 | 核心（自研） |
| SkinsRestorer | 15.12.5 | 3 | 3 | 皮肤 |
| Vault | 1.7.3-b131 | 2 | 1 | 经济接口 |
| ViaBackwards | 5.11.0 | 0 | 0 | 版本兼容 |
| ViaRewind | 4.1.3 | 0 | 0 | 版本兼容 |
| ViaVersion | 5.11.0 | 2 | 1 | 版本兼容 |
| DeathChest | 3.0.1 | 0 | 9 | 死亡箱 |
| GrimAC | 2.3.74-58c8b92 | 0 | 14 | 反作弊 |
| packetevents | 2.13.0 | 1 | 1 | 内部库 |
| voicechat | 2.6.21 | 1 | 4 | 语音 |
| WorldEdit | 7.4.5+7590-b8dc4c1 | 19 | 17 | 建筑编辑 |
| WorldGuard | 7.0.18+2392-fa605e6 | 7 | 8 | 领地保护 |

## 1. BackOnDeath v0.4

- 文件：`BackOnDeath.jar`（plugin.yml）
- 指令 1 个 / 权限节点 2 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `back` | - | Teleport to your last death location. | `-` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `bod.back` | Permissions to /back | True | - |
| `bod.bypass` | Permissions to ignore vault charge | op | - |

## 2. Essentials v2.22.0

- 文件：`EssentialsX-2.22.0.jar`（plugin.yml）
- 指令 153 个 / 权限节点 453 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `afk` | eafk,away,eaway | Marks you as away-from-keyboard. | `-` |
| `antioch` | eantioch,grenade,egrenade,tnt,etnt | A little surprise for operators. | `-` |
| `anvil` | eanvil | Opens up an Anvil. | `-` |
| `back` | eback,return,ereturn | Teleports you to your location prior to tp/spawn/warp. | `-` |
| `backup` | ebackup | Runs the backup if configured. | `-` |
| `balance` | bal,ebal,ebalance,money,emoney | States the current balance of a player. | `-` |
| `balancetop` | ebalancetop,baltop,ebaltop | Gets the top balance values. | `-` |
| `ban` | eban | Bans a player. | `-` |
| `banip` | ebanip | Bans an IP address. | `-` |
| `beezooka` | ebeezooka,beecannon,ebeecannon | Throw an exploding bee at your opponent. | `-` |
| `bigtree` | ebigtree,largetree,elargetree | Spawn a big tree where you are looking. | `-` |
| `book` | ebook | Allows reopening and editing of sealed books. | `-` |
| `bottom` | ebottom | Teleport to the lowest block at your current position. | `-` |
| `break` | ebreak | Breaks the block you are looking at. | `-` |
| `broadcast` | bc,ebc,bcast,ebcast,ebroadcast,shout,eshout | Broadcasts a message to the entire server. | `-` |
| `broadcastworld` | bcw,ebcw,bcastw,ebcastw,ebroadcastworld,shoutworld,eshoutworld | Broadcasts a message to a world. | `-` |
| `burn` | eburn | Set a player on fire. | `-` |
| `cartographytable` | ecartographytable,carttable,ecarttable | Opens up a cartography table. | `-` |
| `clearinventory` | ci,eci,clean,eclean,clear,eclear,clearinvent,eclearinvent,eclearinventory | Clear all items in your inventory. | `-` |
| `clearinventoryconfirmtoggle` | eclearinventoryconfirmtoggle,clearinventoryconfirmoff,eclearinventoryconfirmoff,clearconfirmoff,eclearconfirmoff,clearconfirmon,eclearconfirmon,clearconfirm,eclearconfirm | Toggles whether you are prompted to confirm inventory clears. | `-` |
| `compass` | ecompass,direction,edirection | Describes your current bearing. | `-` |
| `condense` | econdense,compact,ecompact,blocks,eblocks,toblocks,etoblocks | Condenses items into a more compact blocks. | `-` |
| `createkit` | kitcreate,createk,kc,ck | Create a kit in game! | `-` |
| `customtext` | - | Allows you to create custom text commands. | `-` |
| `delhome` | edelhome,remhome,eremhome,rmhome,ermhome | Removes a home. | `-` |
| `deljail` | edeljail,remjail,eremjail,rmjail,ermjail | Removes a jail. | `-` |
| `delkit` | edelkit,remkit,eremkit,rmkit,ermkit,deletekit,edeletekit | Deletes the specified kit. | `-` |
| `delwarp` | edelwarp,remwarp,eremwarp,rmwarp,ermwarp | Deletes the specified warp. | `-` |
| `depth` | edepth,height,eheight | States current depth, relative to sea level. | `-` |
| `disposal` | edisposal,trash,etrash | Opens a portable disposal menu. | `-` |
| `eco` | eeco,economy,eeconomy | Manages the server economy. | `-` |
| `editsign` | sign,esign,eeditsign | Edits a sign in the world. | `-` |
| `enchant` | eenchant,enchantment,eenchantment | Enchants the item the user is holding. | `-` |
| `enderchest` | echest,eechest,eenderchest,endersee,eendersee,ec,eec | Lets you see inside an enderchest. | `-` |
| `essentials` | eessentials,ess,eess,essversion | Reloads essentials. | `-` |
| `exp` | eexp,xp | Give, set, reset, or look at a players experience. | `-` |
| `ext` | eext,extinguish,eextinguish | Extinguish players. | `-` |
| `feed` | eat,eeat,efeed | Satisfy the hunger. | `-` |
| `fireball` | efireball,fireentity,efireentity,fireskull,efireskull | Throw a fireball or other assorted projectiles. | `-` |
| `firework` | efirework | Allows you to modify a stack of fireworks. | `-` |
| `fly` | efly | Take off, and soar! | `-` |
| `gamemode` | adventure,eadventure,adventuremode,eadventuremode,creative,ecreative,eecreative,creativemode,ecreativemode,egamemode,gm,egm,gma,egma,gmc,egmc,gms,egms,gmt,egmt,survival,esurvival,survivalmode,esurvivalmode,gmsp,sp,egmsp,spec,spectator | Change player gamemode. | `-` |
| `gc` | lag,elag,egc,mem,emem,memory,ememory,uptime,euptime,tps,etps,entities,eentities | Reports memory, uptime and tick info. | `-` |
| `getpos` | coords,egetpos,position,eposition,whereami,ewhereami,getlocation,egetlocation,getloc,egetloc | Get your current coordinates or those of a player. | `-` |
| `give` | egive | Give a player an item. | `-` |
| `god` | egod,godmode,egodmode,tgm,etgm | Enables your godly powers. | `-` |
| `grindstone` | egrindstone | Opens up a grindstone. | `-` |
| `hat` | ehat,head,ehead | Get some cool new headgear. | `-` |
| `heal` | eheal | Heals you or the given player. | `-` |
| `help` | ehelp | Views a list of available commands. | `-` |
| `helpop` | ac,eac,amsg,eamsg,ehelpop | Message online admins. | `-` |
| `home` | ehome,homes,ehomes | Teleport to your home. | `-` |
| `ice` | eice,efreeze | Cools a player off. | `-` |
| `ignore` | eignore,unignore,eunignore,delignore,edelignore,remignore,eremignore,rmignore,ermignore | Ignore or unignore other players. | `-` |
| `info` | about,eabout,ifo,eifo,einfo,inform,einform,news,enews | Shows information set by the server owner. | `-` |
| `invsee` | einvsee | See the inventory of other players. | `-` |
| `item` | i,eitem,ei | Spawn an item. | `-` |
| `itemdb` | dura,edura,durability,edurability,eitemdb,itemno,eitemno | Searches for an item. | `-` |
| `itemlore` | lore,elore,ilore,eilore,eitemlore | Edit the lore of an item. | `-` |
| `itemname` | iname,einame,eitemname,itemrename,irename,eitemrename,eirename | Names an item. | `-` |
| `jailedplayers` | ejailedplayers,ejailed,ejp | List all jailed players. | `-` |
| `jails` | ejails | List all jails. | `-` |
| `jump` | j,ej,ejump,jumpto,ejumpto | Jumps to the nearest block in the line of sight. | `-` |
| `kick` | ekick | Kicks a specified player with a reason. | `-` |
| `kickall` | ekickall | Kicks all players off the server except the issuer. | `-` |
| `kill` | ekill | Kills specified player. | `-` |
| `kit` | ekit,kits,ekits | Obtains the specified kit or views all available kits. | `-` |
| `kitreset` | ekitreset,kitr,ekitr,resetkit,eresetkit | Resets the cooldown on the specified kit. | `-` |
| `kittycannon` | ekittycannon | Throw an exploding kitten at your opponent. | `-` |
| `lightning` | elightning,shock,eshock,smite,esmite,strike,estrike,thor,ethor | The power of Thor. Strike at cursor or player. | `-` |
| `list` | elist,online,eonline,playerlist,eplayerlist,plist,eplist,who,ewho | List all online players. | `-` |
| `loom` | eloom | Opens up a loom. | `-` |
| `mail` | email,eemail,memo,ememo | Manages inter-player, intra-server mail. | `-` |
| `me` | action,eaction,describe,edescribe,eme | Describes an action in the context of the player. | `-` |
| `more` | emore | Fills the item stack in hand to specified amount, or to maximum size if none is specified. | `-` |
| `motd` | emotd | Views the Message Of The Day. | `-` |
| `msg` | w,m,t,pm,emsg,epm,tell,etell,whisper,ewhisper | Sends a private message to the specified player. | `-` |
| `msgtoggle` | emsgtoggle | Blocks receiving all private messages. | `-` |
| `mute` | emute,silence,esilence,unmute,eunmute | Mutes or unmutes a player. | `-` |
| `near` | enear,nearby,enearby | Lists the players near by or around a player. | `-` |
| `nick` | enick,nickname,enickname | Change your nickname or that of another player. | `-` |
| `nuke` | enuke | May death rain upon them. | `-` |
| `pay` | epay | Pays another player from your balance. | `-` |
| `payconfirmtoggle` | epayconfirmtoggle,payconfirmoff,epayconfirmoff,payconfirmon,epayconfirmon,payconfirm,epayconfirm | Toggles whether you are prompted to confirm payments. | `-` |
| `paytoggle` | epaytoggle,payoff,epayoff,payon,epayon | Toggles whether you are accepting payments. | `-` |
| `ping` | echo,eecho,eping,pong,epong | Pong! | `-` |
| `playtime` | eplaytime | Shows a player's time played in game | `-` |
| `potion` | epotion,elixer,eelixer | Adds custom potion effects to a potion. | `-` |
| `powertool` | epowertool,pt,ept | Assigns a command to the item in hand. | `-` |
| `powertoollist` | epowertoollist,ptlist,eptlist | Lists all current powertools. | `-` |
| `powertooltoggle` | epowertooltoggle,ptt,eptt,pttoggle,epttoggle | Enables or disables all current powertools. | `-` |
| `ptime` | playertime,eplayertime,eptime | Adjust player's client time. Add @ prefix to fix. | `-` |
| `pweather` | playerweather,eplayerweather,epweather | Adjust a player's weather | `-` |
| `r` | er,reply,ereply | Quickly reply to the last player to message you. | `-` |
| `realname` | erealname | Displays the username of a user based on nick. | `-` |
| `recipe` | formula,eformula,method,emethod,erecipe,recipes,erecipes | Displays how to craft items. | `-` |
| `remove` | eremove,butcher,ebutcher,killall,ekillall,mobkill,emobkill | Removes entities in your world. | `-` |
| `renamehome` | erenamehome | Renames a home. | `-` |
| `repair` | fix,efix,erepair | Repairs the durability of one or all items. | `-` |
| `rest` | erest | Rests you or the given player. | `-` |
| `rtoggle` | ertoggle,replytoggle,ereplytoggle | Change whether the recipient of the reply is last recipient or last sender | `-` |
| `rules` | erules | Views the server rules. | `-` |
| `seen` | eseen,ealts,alts | Shows the last logout time of a player. | `-` |
| `sell` | esell | Sells the item currently in your hand. | `-` |
| `sethome` | esethome,createhome,ecreatehome | Set your home to your current location. | `-` |
| `setjail` | esetjail,createjail,ecreatejail | Creates a jail where you specified named [jailname]. | `-` |
| `settpr` | esettpr,settprandom,esettprandom | Set the random teleport location and parameters. | `-` |
| `setwarp` | createwarp,ecreatewarp,esetwarp | Creates a new warp. | `-` |
| `setworth` | esetworth | Set the sell value of an item. | `-` |
| `showkit` | kitpreview,preview,kitshow | Show contents of a kit. | `-` |
| `skull` | eskull,playerskull,eplayerskull,head,ehead | Set the owner of a player skull | `-` |
| `smithingtable` | esmithingtable,smithtable,esmithtable | Opens up a smithing table. | `-` |
| `socialspy` | esocialspy | Toggles if you can see msg/mail commands in chat. | `-` |
| `spawner` | changems,echangems,espawner,mobspawner,emobspawner | Change the mob type of a spawner. | `-` |
| `spawnmob` | mob,emob,spawnentity,espawnentity,espawnmob | Spawns a mob. | `-` |
| `speed` | flyspeed,eflyspeed,fspeed,efspeed,espeed,walkspeed,ewalkspeed,wspeed,ewspeed | Change your speed limits. | `-` |
| `stonecutter` | estonecutter | Opens up a stonecutter. | `-` |
| `sudo` | esudo | Make another user perform a command. | `-` |
| `suicide` | esuicide | Causes you to perish. | `-` |
| `tempban` | etempban | Temporary ban a user. | `-` |
| `tempbanip` | etempbanip | Temporarily ban an IP Address. | `-` |
| `thunder` | ethunder | Enable/disable thunder. | `-` |
| `time` | day,eday,night,enight,etime | Display/Change the world time. Defaults to current world. | `-` |
| `togglejail` | jail,ejail,tjail,etjail,etogglejail,unjail,eunjail | Jails/Unjails a player, TPs them to the jail specified. | `-` |
| `top` | etop | Teleport to the highest block at your current position. | `-` |
| `tp` | tele,etele,teleport,eteleport,etp,tp2p,etp2p | Teleport to a player. | `-` |
| `tpa` | call,ecall,etpa,tpask,etpask | Request to teleport to the specified player. | `-` |
| `tpaall` | etpaall | Requests all players online to teleport to you. | `-` |
| `tpacancel` | etpacancel | Cancel all outstanding teleport requests. Specify [player] to cancel requests with them. | `-` |
| `tpaccept` | etpaccept,tpyes,etpyes | Accepts teleport requests. | `-` |
| `tpahere` | etpahere | Request that the specified player teleport to you. | `-` |
| `tpall` | etpall | Teleport all online players to another player. | `-` |
| `tpauto` | etpauto | Automatically accept teleportation requests. | `-` |
| `tpdeny` | etpdeny,tpno,etpno | Rejects teleport requests. | `-` |
| `tphere` | s,etphere | Teleport a player to you. | `-` |
| `tpo` | etpo | Teleport override for tptoggle. | `-` |
| `tpoffline` | otp,offlinetp,tpoff,tpoffline,etpoffline | Teleport to a player's last known logout location | `-` |
| `tpohere` | etpohere | Teleport here override for tptoggle. | `-` |
| `tppos` | etppos | Teleport to coordinates. | `-` |
| `tpr` | etpr,tprandom,etprandom | Teleport randomly. | `-` |
| `tptoggle` | etptoggle | Blocks all forms of teleportation. | `-` |
| `tree` | etree | Spawn a tree where you are looking. | `-` |
| `unban` | pardon,eunban,epardon | Unbans the specified player. | `-` |
| `unbanip` | eunbanip,pardonip,epardonip | Unbans the specified IP address. | `-` |
| `unlimited` | eunlimited,ul,unl,eul,eunl | Allows the unlimited placing of items. | `-` |
| `vanish` | v,ev,evanish | Hide yourself from other players. | `-` |
| `warp` | ewarp,warps,ewarps | List all warps or warp to the specified location. | `-` |
| `warpinfo` | ewarpinfo | Finds location information for a specified warp. | `-` |
| `weather` | rain,erain,sky,esky,storm,estorm,sun,esun,eweather | Sets the weather. | `-` |
| `whois` | ewhois | Determine basic information about the specified player. | `-` |
| `workbench` | craft,ecraft,wb,ewb,wbench,ewbench,eworkbench | Opens up a workbench. | `-` |
| `world` | eworld | Switch between worlds. | `-` |
| `worth` | eprice,price,eworth | Calculates the worth of items in hand or as specified. | `-` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `essentials.*` | Give players with op everything by default | op | - |
| `essentials.afk` | Allows access to the /afk command | - | - |
| `essentials.afk.auto` | Players with this permission will be set to afk after a period of inaction as defined in the config file | False | - |
| `essentials.afk.kickexempt` | Players with this permission will not be kicked for being AFK | - | - |
| `essentials.afk.message` | Allows the player to set a custom AFK message | - | - |
| `essentials.afk.others` | Allows the player to set another player's AFK status | - | - |
| `essentials.antioch` | Allows access to the /antioch command | - | - |
| `essentials.anvil` | Allows access to the /anvil command | - | - |
| `essentials.back` | Allows access to the /back command | - | - |
| `essentials.back.into.<world>` | Allows the player to use the /back command to travel to a specific world | - | - |
| `essentials.back.ondeath` | Players with this permission will have back location stored during death | False | - |
| `essentials.back.onteleport` | Players with this permission will have back location stored during any teleportation | True | - |
| `essentials.back.others` | Allows access to the /back command for other players | - | - |
| `essentials.backup` | Allows access to the /backup command | - | - |
| `essentials.balance` | Allows access to the /balance command | - | - |
| `essentials.balance.others` | Allows view other players balance with the /balance command | - | - |
| `essentials.balancetop` | Allows access to the /balancetop command | - | - |
| `essentials.balancetop.exclude` | Players with this permission are excluded from the balancetop | False | - |
| `essentials.balancetop.force` | Allows access to force refresh the balancetop list | - | - |
| `essentials.ban` | Allows access to the /ban command | - | - |
| `essentials.ban.exempt` | Prevent a specified group or player from being banned | False | - |
| `essentials.ban.notify` | Allows the bearer to be notified when a player is banned | - | - |
| `essentials.ban.offline` | Allows access to the /ban command for offline players, which may in turn by used to ban exempt players who are offline | - | - |
| `essentials.banip` | Allows access to the /banip command | - | - |
| `essentials.banip.notify` | Allows the bearer to be notified when a player is banned | - | - |
| `essentials.beezooka` | Allows access to the /beezooka command | - | - |
| `essentials.bigtree` | Allows access to the /bigtree command | - | - |
| `essentials.book` | Allows access to the /book command | - | - |
| `essentials.book.author` | Allows access to edit book authors with the /book command | - | - |
| `essentials.book.others` | Allows access to edit other players books with the /book command | - | - |
| `essentials.book.title` | Allows access to edit book titles with the /book command | - | - |
| `essentials.bottom` | Allows access to the /bottom command | - | - |
| `essentials.break` | Allows access to the /break command | - | - |
| `essentials.break.bedrock` | Allows access to the /break command for bedrock | - | - |
| `essentials.broadcast` | Allows access to the /broadcast command | - | - |
| `essentials.broadcastworld` | Allows access to the /broadcastworld command | - | - |
| `essentials.burn` | Allows access to the /burn command | - | - |
| `essentials.cartographytable` | Allows access to the /cartographytable command | - | - |
| `essentials.chat.ignoreexempt` | Someone with this permission will not be ignored, even if they are on another persons ignore list | False | - |
| `essentials.chat.spy` | Allows the bearers to see all local chat messages, regardless of their proximity to the sender | - | - |
| `essentials.chat.spy.exempt` | Allows the bearer to be exempt from the local chat spy permission | - | - |
| `essentials.clearinventory` | Allows access to the /clearinventory command | - | - |
| `essentials.clearinventory.all` | Allows access to clear the inventory of all players with the /clearinventory command | - | - |
| `essentials.clearinventory.others` | Allows access to clear the inventory of other players with the /clearinventory command | - | - |
| `essentials.clearinventoryconfirmtoggle` | Allows access to the /clearinventoryconfirmtoggle command | - | - |
| `essentials.commandcooldowns.bypass` | Allows the bypassing of all command cooldowns | - | - |
| `essentials.commandcooldowns.bypass.<commandname>` | Allows the bypassing of the cooldown for a specific command | - | - |
| `essentials.compass` | Allows access to the /compass command | - | - |
| `essentials.condense` | Allows access to the /condense command | - | - |
| `essentials.createkit` | Allows access to the /createkit command | - | - |
| `essentials.customtext` | Allows access to the /customtext command and all aliases | - | - |
| `essentials.delhome` | Allows access to the /delhome command | - | - |
| `essentials.delhome.others` | Allows access to delete other players homes with the /delhome command | - | - |
| `essentials.deljail` | Allows access to the /deljail command | - | - |
| `essentials.delkit` | Allows access to the /delkit command | - | - |
| `essentials.delwarp` | Allows access to the /delwarp command | - | - |
| `essentials.depth` | Allows access to the /depth command | - | - |
| `essentials.disposal` | Allows access to the /disposal command | - | - |
| `essentials.eco` | Allows access to the /eco command | - | - |
| `essentials.eco.loan` | Allows the bearer to possess a negative balance | - | - |
| `essentials.editsign` | Allows access to the /editsign command | - | - |
| `essentials.editsign.color` | Allows the bearer to use color codes on signs | - | - |
| `essentials.editsign.format` | Allows the bearer to use formatting codes on signs | - | - |
| `essentials.editsign.magic` | Allows the bearer to use magic codes on signs | - | - |
| `essentials.editsign.rgb` | Allows the bearer to use RGB codes on signs | - | - |
| `essentials.editsign.unlimited` | Allows the bearer to exceed the 15 character limit on signs | - | - |
| `essentials.editsign.waxed.exempt` | Allows the bearer to edit waxed signs | - | - |
| `essentials.enchant` | Allows access to the /enchant command | - | - |
| `essentials.enchantments.<enchantment>` | Allows the bearer to use a specific enchantment with the /enchant command | - | - |
| `essentials.enchantments.allowunsafe` | Allows the bearer to enchant items with unsafe enchantments | - | - |
| `essentials.enderchest` | Allows access to the /enderchest command | - | - |
| `essentials.enderchest.modify` | Allows the bearer to modify other players enderchests | - | - |
| `essentials.enderchest.others` | Allows access to the /enderchest command for other players | - | - |
| `essentials.essentials` | Allows access to the /essentials command | - | - |
| `essentials.exempt` | Parent permission to be exempt from many moderator actions | False | - |
| `essentials.exp` | Allows access to the /exp command | - | - |
| `essentials.exp.give` | Allows the bearer to give experience to themselves | - | - |
| `essentials.exp.give.others` | Allows the bearer to give experience to other players | - | - |
| `essentials.exp.others` | Allows the bearer to view other players experience | - | - |
| `essentials.exp.set` | Allows the bearer to set experience for themselves | - | - |
| `essentials.exp.set.others` | Allows the bearer to set experience for other players | - | - |
| `essentials.ext` | Allows access to the /ext command | - | - |
| `essentials.ext.others` | Allows access to the /ext command for other players | - | - |
| `essentials.feed` | Allows access to the /feed command | - | - |
| `essentials.feed.others` | Allows access to the /feed command for other players | - | - |
| `essentials.fireball` | Allows access to the /fireball command. Additional permissions are required for each type of fireball. | - | - |
| `essentials.fireball.arrow` | Allows access to use the arrows in the /fireball command | - | - |
| `essentials.fireball.dragon` | Allows access to use the dragon in the /fireball command | - | - |
| `essentials.fireball.egg` | Allows access to use the egg in the /fireball command | - | - |
| `essentials.fireball.fireball` | Allows access to use the fireball in the /fireball command | - | - |
| `essentials.fireball.large` | Allows access to use the large fireball in the /fireball command | - | - |
| `essentials.fireball.lingeringpotion` | Allows access to use the lingering potion in the /fireball command | - | - |
| `essentials.fireball.skull` | Allows access to use the skull in the /fireball command | - | - |
| `essentials.fireball.small` | Allows access to use the small fireball in the /fireball command | - | - |
| `essentials.fireball.snowball` | Allows access to use the snowball in the /fireball command | - | - |
| `essentials.fireball.splashpotion` | Allows access to use the splash potion in the /fireball command | - | - |
| `essentials.fireball.trident` | Allows access to use the trident in the /fireball command | - | - |
| `essentials.firework` | Allows access to the /firework command | - | - |
| `essentials.firework.fire` | Allows the bearer to use the firework command to launch a copy of the firework in hand | - | - |
| `essentials.firework.multiple` | Allows the bearer to use the firework command to launch multiple fireworks | - | - |
| `essentials.fly` | Allows access to the /fly command | - | - |
| `essentials.fly.others` | Allows access to the /fly command for other players | - | - |
| `essentials.fly.safelogin` | Bearers of this permission will be put into fly mode if they log in while in the air | - | - |
| `essentials.gamemode` | Allows access to the /gamemode command | - | - |
| `essentials.gamemode.*` | Allows access to all gamemodes with the /gamemode command | op | - |
| `essentials.gamemode.adventure` | Allows access to the adventure gamemode with the /gamemode command | - | - |
| `essentials.gamemode.all` | Allows access to all gamemodes with the /gamemode command | - | - |
| `essentials.gamemode.creative` | Allows access to the creative gamemode with the /gamemode command | - | - |
| `essentials.gamemode.others` | Allows access to the /gamemode command for other players | - | - |
| `essentials.gamemode.spectator` | Allows access to the spectator gamemode with the /gamemode command | - | - |
| `essentials.gamemode.survival` | Allows access to the survival gamemode with the /gamemode command | - | - |
| `essentials.gc` | Allows access to the /gc command | - | - |
| `essentials.getpos` | Allows access to the /getpos command | - | - |
| `essentials.getpos.others` | Allows access to the /getpos command for other players | - | - |
| `essentials.give` | Allows access to the /give command | - | - |
| `essentials.give.item-<item-name>` | Allows access to the /give command for a specific item when permission-based-item-spawn is enabled | - | - |
| `essentials.give.item-all` | Allows access to the /give command for all items when permission-based-item-spawn is enabled | - | - |
| `essentials.god` | Allows access to the /god command | - | - |
| `essentials.god.others` | Allows access to the /god command for other players | - | - |
| `essentials.god.pvp` | Allows the bearer to attack players while in god mode | - | - |
| `essentials.grindstone` | Allows access to the /grindstone command | - | - |
| `essentials.hat` | Allows access to the /hat command | - | - |
| `essentials.hat.ignore-binding` | Allows the bearer to use the /hat command when they have equipped an item with curse of binding | - | - |
| `essentials.hat.prevent-type.<item-name>` | Prevents the player from using the /hat command with the specified item | - | - |
| `essentials.heal` | Allows access to the /heal command | - | - |
| `essentials.heal.others` | Allows access to the /heal command for other players | - | - |
| `essentials.help` | Allows access to the /help command | - | - |
| `essentials.help.<plugin-name>` | Allows access to the /help command for a specific plugin | - | - |
| `essentials.helpop` | Allows access to the /helpop command | - | - |
| `essentials.helpop.receive` | Allows the bearer to receive helpop messages | - | - |
| `essentials.home` | Allows access to the /home command | - | - |
| `essentials.home.bed` | Allows access to the /home command for beds | - | - |
| `essentials.home.compass` | Point the player's compass at their first home. compass-towards-home-perm needs to be enabled in the configuration. | False | - |
| `essentials.home.others` | Allows access to teleport to other players homes with the /home command | - | - |
| `essentials.ice` | Allows access to the /ice command | - | - |
| `essentials.ice.others` | Allows access to the /ice command for other players | - | - |
| `essentials.ignore` | Allows access to the /ignore command | - | - |
| `essentials.info` | Allows access to the /info command | - | - |
| `essentials.invsee` | Allows access to the /invsee command | - | - |
| `essentials.invsee.equip` | Allows access to view items in armor slots with the /invsee command | - | - |
| `essentials.invsee.modify` | Allows access to modify items in other players inventories with the /invsee command | - | - |
| `essentials.invsee.preventmodify` | Prevents other players from modifying the players inventory. | False | - |
| `essentials.item` | Allows access to the /item command | - | - |
| `essentials.itemdb` | Allows access to the /itemdb command | - | - |
| `essentials.itemlore` | Allows access to the /itemlore command | - | - |
| `essentials.itemname` | Allows access to the /itemname command | - | - |
| `essentials.itemname.color` | Allows access to the /itemname command with color text | - | - |
| `essentials.itemname.format` | Allows access to the /itemname command with formatting text | - | - |
| `essentials.itemname.magic` | Allows access to the /itemname command with magic text | - | - |
| `essentials.itemname.prevent-type.<item-name>` | Prevents the player from using the /itemname command with the specified item | - | - |
| `essentials.itemname.rgb` | Allows access to the /itemname command with RGB text | - | - |
| `essentials.itemspawn.exempt` | Allows the bearer to spawn items in the item blacklist | - | - |
| `essentials.itemspawn.meta-author` | Allows the bearer to spawn items with author metadata | - | - |
| `essentials.itemspawn.meta-book` | Allows the bearer to spawn items with pre-filled content from book.txt | - | - |
| `essentials.itemspawn.meta-chapter-<chapter>` | Allows the bearer to spawn specific books only, from book.txt. with the /give command. | - | - |
| `essentials.itemspawn.meta-firework` | Allows the bearer to spawn items with firework metadata | - | - |
| `essentials.itemspawn.meta-head` | Allows the bearer to spawn items with head metadata | - | - |
| `essentials.itemspawn.meta-lore` | Allows the bearer to spawn items with lore metadata | - | - |
| `essentials.itemspawn.meta-title` | Allows the bearer to spawn items with title metadata | - | - |
| `essentials.jail.allow-block-damage` | Allows the bearer to damage blocks while jailed | - | - |
| `essentials.jail.allow-break` | Allows the bearer to break blocks while jailed | - | - |
| `essentials.jail.allow-interact` | Allows the bearer to interact with blocks while jailed | - | - |
| `essentials.jail.allow-place` | Allows the bearer to place blocks while jailed | - | - |
| `essentials.jail.allow.<command>` | Allows the bearer to use the specified command while jailed | - | - |
| `essentials.jail.exempt` | Prevent a specified group or player from being jailed | - | - |
| `essentials.jail.notify` | Allows the bearer to be notified when other players are jailed | - | - |
| `essentials.jailedplayers` | Allows access to the /jailedplayers command | - | - |
| `essentials.jails` | Allows access to the /jails command | - | - |
| `essentials.joinfullserver` | Allows the to join the server even if it is full | - | - |
| `essentials.jump` | Allows access to the /jump command | - | - |
| `essentials.jump.lock` | Allows access to the /jump lock command | - | - |
| `essentials.keepinv` | Controls whether players keep their inventory on death. | False | - |
| `essentials.keepxp` | Allows the user to keep their exp on death, instead of dropping it. | False | - |
| `essentials.kick` | Allows access to the /kick command | - | - |
| `essentials.kick.exempt` | Prevents the player from being kicked. | False | - |
| `essentials.kick.notify` | Allows the bearer to be notified when other players are kicked | - | - |
| `essentials.kickall` | Allows access to the /kickall command | - | - |
| `essentials.kickall.exempt` | Prevents the player from being kicked by /kickall | - | - |
| `essentials.kill` | Allows access to the /kill command | - | - |
| `essentials.kill.exempt` | Prevents the player from being killed by /kill | - | - |
| `essentials.kill.force` | Allows the bearer to be killed by /kill even if their death is canceled | - | - |
| `essentials.kit` | Allows access to the /kit command | - | - |
| `essentials.kit.exemptdelay` | Exempts you from the kit delay feature, this affects signs as well as command. | False | - |
| `essentials.kit.others` | Allows access to the /kit command for other players | - | - |
| `essentials.kitreset` | Allows access to the /kitreset command | - | - |
| `essentials.kitreset.others` | Allows access to reset other players kits with the /kitreset command | - | - |
| `essentials.kits.*` | Allows access to all kits | - | - |
| `essentials.kits.<kit-name>` | Allows access to a specific kit | - | - |
| `essentials.kittycannon` | Allows access to the /kittycannon command | - | - |
| `essentials.lightning` | Allows access to the /lightning command | - | - |
| `essentials.lightning.others` | Allows access to the /lightning command for other players | - | - |
| `essentials.list` | Allows access to the /list command | - | - |
| `essentials.list.hidden` | Allow access to view hidden players in the /list command | - | - |
| `essentials.loom` | Allows access to the /loom command | - | - |
| `essentials.mail` | Allows access to the /mail command | - | - |
| `essentials.mail.clear.others` | Allows access to clear other players mail with the /mail command | - | - |
| `essentials.mail.clearall` | Allows access to clear all mail with the /mail command | - | - |
| `essentials.mail.send` | Allows access to send mail with the /mail command | - | - |
| `essentials.mail.sendall` | Allows access to send mail to all players with the /mail command | - | - |
| `essentials.mail.sendtemp` | Allows access to send temporary mail with the /mail command | - | - |
| `essentials.me` | Allows access to the /me command | - | - |
| `essentials.more` | Allows access to the /more command | - | - |
| `essentials.motd` | Allows access to the /motd command | - | - |
| `essentials.msg` | Allows access to the /msg command | - | - |
| `essentials.msg.color` | Allows access to the /msg command with color text | - | - |
| `essentials.msg.format` | Allows access to the /msg command with formatting text | - | - |
| `essentials.msg.magic` | Allows access to the /msg command with magic text | - | - |
| `essentials.msg.multiple` | Allows access to send messages to multiple players with the /msg command | - | - |
| `essentials.msg.rgb` | Allows access to the /msg command with RGB text | - | - |
| `essentials.msg.url` | Allows access to send URLs in the /msg command | - | - |
| `essentials.msgtoggle` | Allows access to the /msgtoggle command | - | - |
| `essentials.msgtoggle.bypass` | Allows the bearer to bypass the msgtoggle setting for other players | - | - |
| `essentials.msgtoggle.others` | Allows access to the /msgtoggle command for other players | - | - |
| `essentials.mute` | Allows access to the /mute command | - | - |
| `essentials.mute.exempt` | Prevent a specified group or player from being muted | False | - |
| `essentials.mute.notify` | Allows the bearer to be notified when other players are muted | - | - |
| `essentials.mute.offline` | Allows access to mute offline players | - | - |
| `essentials.mute.unlimited` | Allows the bearer to override the max-mute-time setting | - | - |
| `essentials.near` | Allows access to the /near command | - | - |
| `essentials.near.exclude` | If the player should be excluded from near lookups. | False | - |
| `essentials.near.maxexempt` | Allows the bearer to bypass the radius limit for the /near command | - | - |
| `essentials.near.others` | Allows access to the /near command for other players | - | - |
| `essentials.nick` | Allows access to the /nick command | - | - |
| `essentials.nick.allowunsafe` | If a player has this, they can set their username to any value. Use with caution, as this has the potential to break userdata files. | False | - |
| `essentials.nick.blacklist.bypass` | Allows the bearer to bypass the nickname blacklist | - | - |
| `essentials.nick.changecolors` | Allows the bearer to change **only** the color of their nickname | - | - |
| `essentials.nick.color` | Allows access to the /nick command with color text | - | - |
| `essentials.nick.format` | Allows access to the /nick command with formatting text | - | - |
| `essentials.nick.hideprefix` | Players with this permission will not have the nickname prefix applied to them | False | - |
| `essentials.nick.magic` | Allows access to the /nick command with magic text | - | - |
| `essentials.nick.others` | Allows access to the /nick command for other players | - | - |
| `essentials.nick.rgb` | Allows access to the /nick command with RGB text | - | - |
| `essentials.nocommandcost.<command>` | Allows the bearer to use the specified command without cost | - | - |
| `essentials.nocommandcost.all` | Allows the bearer to use all commands without cost | - | - |
| `essentials.nuke` | Allows access to the /nuke command | - | - |
| `essentials.oversizedstacks` | Allows the bearer to spawn oversized stacks | - | - |
| `essentials.pay` | Allows access to the /pay command | - | - |
| `essentials.pay.multiple` | Allows access to pay multiple players with the /pay command | - | - |
| `essentials.pay.offline` | Allows access to pay offline players with the /pay command | - | - |
| `essentials.payconfirmtoggle` | Allows access to the /payconfirmtoggle command | - | - |
| `essentials.paytoggle` | Allows access to the /paytoggle command | - | - |
| `essentials.ping` | Allows access to the /ping command | - | - |
| `essentials.playtime` | Allows access to the /playtime command | - | - |
| `essentials.playtime.others` | Allows access to the /playtime command for other players | - | - |
| `essentials.potion` | Allows access to the /potion command | - | - |
| `essentials.potion.<potion-type>` | Allows access to the /potion command for a specific potion type | - | - |
| `essentials.potion.apply` | Allows access to the /potion apply command | - | - |
| `essentials.powertool` | Allows access to the /powertool command | - | - |
| `essentials.powertool.append` | Allows access to add multiple commands to a powertool | - | - |
| `essentials.powertoollist` | Allows access to the /powertoollist command | - | - |
| `essentials.powertooltoggle` | Allows access to the /powertooltoggle command | - | - |
| `essentials.ptime` | Allows access to the /ptime command | - | - |
| `essentials.ptime.others` | Allows access to the /ptime command for other players | - | - |
| `essentials.pvpdelay.exempt` | Allows the bearer to bypass the pvp delay setting | - | - |
| `essentials.pweather` | Allows access to the /pweather command | - | - |
| `essentials.pweather.others` | Allows access to the /pweather command for other players | - | - |
| `essentials.realname` | Allows access to the /realname command | - | - |
| `essentials.recipe` | Allows access to the /recipe command | - | - |
| `essentials.remove` | Allows access to the /remove command | - | - |
| `essentials.renamehome` | Allows access to the /renamehome command | - | - |
| `essentials.renamehome.others` | Allows access to rename other players homes with the /renamehome command | - | - |
| `essentials.repair` | Allows access to the /repair command | - | - |
| `essentials.repair.all` | Allows access to the /repair all command | - | - |
| `essentials.repair.armor` | Allows access to the /repair armor command | - | - |
| `essentials.repair.enchanted` | Allows access to use the /repair command on enchanted items | - | - |
| `essentials.rest` | Allows access to the /rest command | - | - |
| `essentials.rest.others` | Allows access to the /rest command for other players | - | - |
| `essentials.rtoggle` | Allows access to the /rtoggle command | - | - |
| `essentials.rules` | Allows access to the /rules command | - | - |
| `essentials.seen` | Allows access to the /seen command | - | - |
| `essentials.seen.alts` | Allows access to the /seen command with alts | - | - |
| `essentials.seen.banreason` | Allows access to the /seen command with ban reason | - | - |
| `essentials.seen.extra` | Allows access to the /seen command with extra information | - | - |
| `essentials.seen.firstlogin` | Allows access to the /seen command with first login time | - | - |
| `essentials.seen.ip` | Allows access to the /seen command with IP address | - | - |
| `essentials.seen.ipsearch` | Allows access to use IP addresses with the /seen command | - | - |
| `essentials.seen.location` | Allows access to the /seen command with location | - | - |
| `essentials.seen.uuid` | Allows access to the /seen command with UUID | - | - |
| `essentials.seen.whitelist` | Allows access to the /seen command with whitelist status | - | - |
| `essentials.sell` | Allows access to the /sell command | - | - |
| `essentials.sell.bulk` | Allows access to bulk sell items with the /sell command | - | - |
| `essentials.sell.hand` | Allows access to sell the item in hand with the /sell command | - | - |
| `essentials.sethome` | Allows access to the /sethome command | - | - |
| `essentials.sethome.bed` | Allows the player to right click a bed during daytime to update their 'bed' home. | False | - |
| `essentials.sethome.multiple` | Allows access to set multiple homes with the /sethome command | - | - |
| `essentials.sethome.multiple.<set name>` | Raises the limit of homes to a specific number defined in the config | - | - |
| `essentials.sethome.multiple.unlimited` | Allows access to set unlimited homes with the /sethome command | - | - |
| `essentials.sethome.others` | Allows access to set other players homes with the /sethome command | - | - |
| `essentials.setjail` | Allows access to the /setjail command | - | - |
| `essentials.settpr` | Allows access to the /settpr command | - | - |
| `essentials.setwarp` | Allows access to the /setwarp command | - | - |
| `essentials.setworth` | Allows access to the /setworth command | - | - |
| `essentials.showkit` | Allows access to the /showkit command | - | - |
| `essentials.signs.break.balance` | Allows the bearer to break balance signs | - | - |
| `essentials.signs.break.buy` | Allows the bearer to break buy signs | - | - |
| `essentials.signs.break.disposal` | Allows the bearer to break disposal signs | - | - |
| `essentials.signs.break.enchant` | Allows the bearer to break enchant signs | - | - |
| `essentials.signs.break.free` | Allows the bearer to break free signs | - | - |
| `essentials.signs.break.gamemode` | Allows the bearer to break gamemode signs | - | - |
| `essentials.signs.break.heal` | Allows the bearer to break heal signs | - | - |
| `essentials.signs.break.info` | Allows the bearer to break info signs | - | - |
| `essentials.signs.break.kit` | Allows the bearer to break kit signs | - | - |
| `essentials.signs.break.mail` | Allows the bearer to break mail signs | - | - |
| `essentials.signs.break.protection` | Allows the bearer to break protection signs | - | - |
| `essentials.signs.break.repair` | Allows the bearer to break repair signs | - | - |
| `essentials.signs.break.sell` | Allows the bearer to break sell signs | - | - |
| `essentials.signs.break.spawnmob` | Allows the bearer to break spawnmob signs | - | - |
| `essentials.signs.break.time` | Allows the bearer to break time signs | - | - |
| `essentials.signs.break.trade` | Allows the bearer to break trade signs | - | - |
| `essentials.signs.break.warp` | Allows the bearer to break warp signs | - | - |
| `essentials.signs.break.weather` | Allows the bearer to break weather signs | - | - |
| `essentials.signs.color` | Allows the bearer to create and use color signs | - | - |
| `essentials.signs.create.balance` | Allows the bearer to create balance signs | - | - |
| `essentials.signs.create.buy` | Allows the bearer to create buy signs | - | - |
| `essentials.signs.create.disposal` | Allows the bearer to create disposal signs | - | - |
| `essentials.signs.create.enchant` | Allows the bearer to create enchant signs | - | - |
| `essentials.signs.create.free` | Allows the bearer to create free signs | - | - |
| `essentials.signs.create.gamemode` | Allows the bearer to create gamemode signs | - | - |
| `essentials.signs.create.heal` | Allows the bearer to create heal signs | - | - |
| `essentials.signs.create.info` | Allows the bearer to create info signs | - | - |
| `essentials.signs.create.kit` | Allows the bearer to create kit signs | - | - |
| `essentials.signs.create.mail` | Allows the bearer to create mail signs | - | - |
| `essentials.signs.create.protection` | Allows the bearer to create protection signs | - | - |
| `essentials.signs.create.repair` | Allows the bearer to create repair signs | - | - |
| `essentials.signs.create.sell` | Allows the bearer to create sell signs | - | - |
| `essentials.signs.create.spawnmob` | Allows the bearer to create spawnmob signs | - | - |
| `essentials.signs.create.time` | Allows the bearer to create time signs | - | - |
| `essentials.signs.create.trade` | Allows the bearer to create trade signs | - | - |
| `essentials.signs.create.warp` | Allows the bearer to create warp signs | - | - |
| `essentials.signs.create.weather` | Allows the bearer to create weather signs | - | - |
| `essentials.signs.enchant.allowunsafe` | Allows the bearer to create and use unsafe enchantment signs | - | - |
| `essentials.signs.format` | Allows the bearer to create and use format signs | - | - |
| `essentials.signs.magic` | Allows the bearer to create and use magic signs | - | - |
| `essentials.signs.protection.override` | Allows the bearer to break signs created by other players | - | - |
| `essentials.signs.rgb` | Allows the bearer to create and use RGB signs | - | - |
| `essentials.signs.trade.override` | Allows the bearer to break trade signs created by other players | - | - |
| `essentials.signs.trade.override.collect` | Allows the bearer to collect items from trade signs created by other players | - | - |
| `essentials.signs.use.balance` | Allows the bearer to use balance signs | - | - |
| `essentials.signs.use.buy` | Allows the bearer to use buy signs | - | - |
| `essentials.signs.use.disposal` | Allows the bearer to use disposal signs | - | - |
| `essentials.signs.use.enchant` | Allows the bearer to use enchant signs | - | - |
| `essentials.signs.use.free` | Allows the bearer to use free signs | - | - |
| `essentials.signs.use.gamemode` | Allows the bearer to use gamemode signs | - | - |
| `essentials.signs.use.heal` | Allows the bearer to use heal signs | - | - |
| `essentials.signs.use.info` | Allows the bearer to use info signs | - | - |
| `essentials.signs.use.kit` | Allows the bearer to use kit signs | - | - |
| `essentials.signs.use.mail` | Allows the bearer to use mail signs | - | - |
| `essentials.signs.use.protection` | Allows the bearer to use protection signs | - | - |
| `essentials.signs.use.repair` | Allows the bearer to use repair signs | - | - |
| `essentials.signs.use.sell` | Allows the bearer to use sell signs | - | - |
| `essentials.signs.use.spawnmob` | Allows the bearer to use spawnmob signs | - | - |
| `essentials.signs.use.time` | Allows the bearer to use time signs | - | - |
| `essentials.signs.use.trade` | Allows the bearer to use trade signs | - | - |
| `essentials.signs.use.warp` | Allows the bearer to use warp signs | - | - |
| `essentials.signs.use.weather` | Allows the bearer to use weather signs | - | - |
| `essentials.silentjoin` | Allow to join silently | False | - |
| `essentials.silentjoin.vanish` | Allow to join silently, and get put in vanish mode | False | - |
| `essentials.silentquit` | Suppress leave/quit messages for users with this permission. | False | - |
| `essentials.skull` | Allows access to the /skull command | - | - |
| `essentials.skull.modify` | Allows access to modify other players skulls with the /skull command | - | - |
| `essentials.skull.others` | Allows access to creating other players skulls with the /skull command | - | - |
| `essentials.skull.spawn` | Allows access to spawn a skull with the /skull command | - | - |
| `essentials.sleepingignored` | Allows the bearer to not be required to sleep to skip the night | - | - |
| `essentials.smithingtable` | Allows access to the /smithingtable command | - | - |
| `essentials.socialspy` | Allows access to the /socialspy command | - | - |
| `essentials.socialspy.others` | Allows access to the /socialspy command for other players | - | - |
| `essentials.spawner` | Allows access to the /spawner command | - | - |
| `essentials.spawner.*` | Allows access to set the type of a spawner with the /spawner command to all types | - | - |
| `essentials.spawner.<mob-type>` | Allows access to set the type of a spawner with the /spawner command to a specific type | - | - |
| `essentials.spawner.delay` | Allows access to set the delay of a spawner with the /spawner command | - | - |
| `essentials.spawnerconvert.*` | Allows the bearer to place spawners of any type | - | - |
| `essentials.spawnerconvert.<mob-type>` | Allows the bearer to place spawners of a specific type | - | - |
| `essentials.spawnmob` | Allows access to the /spawnmob command | - | - |
| `essentials.spawnmob.*` | Allows access to spawn all mobs with the /spawnmob command | - | - |
| `essentials.spawnmob.<mob-type>` | Allows access to spawn a specific mob with the /spawnmob command | - | - |
| `essentials.spawnmob.stack` | Allows access to spawn mobs in stacks with the /spawnmob command | - | - |
| `essentials.speed` | Allows access to the /speed command | - | - |
| `essentials.speed.bypass` | Allows the bearer to bypass the speed limit set in the config | - | - |
| `essentials.speed.fly` | Allows access to the /speed command for fly speed | - | - |
| `essentials.speed.others` | Allows access to the /speed command for other players | - | - |
| `essentials.speed.walk` | Allows access to the /speed command for walk speed | - | - |
| `essentials.stonecutter` | Allows access to the /stonecutter command | - | - |
| `essentials.sudo` | Allows access to the /sudo command | - | - |
| `essentials.sudo.exempt` | Prevents the player from being sudo'ed by another user | False | - |
| `essentials.sudo.multiple` | Allows access to the /sudo command for multiple players | - | - |
| `essentials.suicide` | Allows access to the /suicide command for multiple players | - | - |
| `essentials.teleport.cooldown.bypass.back` | If the player does not have this permission, /back will have cooldown even with the parent bypass perm | True | - |
| `essentials.teleport.cooldown.bypass.tpa` | If the player does not have this permission, /tpa will have cooldown even with the parent bypass perm | True | - |
| `essentials.teleport.timer.bypass` | Allows the bearer to bypass the teleport delay | - | - |
| `essentials.teleport.timer.move` | Allows the bearer to move while waiting for a teleport | - | - |
| `essentials.tempban` | Allows access to the /tempban command | - | - |
| `essentials.tempban.exempt` | Prevent a specified group or player from being tempbanned | False | - |
| `essentials.tempban.offline` | Allows access to tempban offline players | - | - |
| `essentials.tempban.unlimited` | Allows the bearer to override the max-tempban-time setting | - | - |
| `essentials.tempbanip` | Allows access to the /tempbanip command | - | - |
| `essentials.thunder` | Allows access to the /thunder command | - | - |
| `essentials.time` | Allows access to the /time command | - | - |
| `essentials.time.set` | Allows access to set the time with the /time command | - | - |
| `essentials.time.world.all` | Allows access to set the time for all worlds with the /time command | - | - |
| `essentials.togglejail` | Allows access to the /togglejail command | - | - |
| `essentials.togglejail.offline` | Allows access to the /togglejail command for offline players | - | - |
| `essentials.top` | Allows access to the /top command | - | - |
| `essentials.tp` | Allows access to the /tp command | - | - |
| `essentials.tp.others` | Allows access to teleporting to other users with the /tp command | - | - |
| `essentials.tp.position` | Allows access to teleporting to a position with the /tp command | - | - |
| `essentials.tpa` | Allows access to the /tpa command | - | - |
| `essentials.tpaall` | Allows access to the /tpaall command | - | - |
| `essentials.tpacancel` | Allows access to the /tpaccept command | - | - |
| `essentials.tpaccept` | Allows access to the /tpaccept command | - | - |
| `essentials.tpahere` | Allows access to the /tpahere command | - | - |
| `essentials.tpall` | Allows access to the /tpall command | - | - |
| `essentials.tpauto` | Allows access to the /tpauto command | - | - |
| `essentials.tpauto.others` | Allows access to the /tpauto command for other players | - | - |
| `essentials.tpdeny` | Allows access to the /tpdeny command | - | - |
| `essentials.tphere` | Allows access to the /tphere command | - | - |
| `essentials.tpo` | Allows access to the /tpo command | - | - |
| `essentials.tpoffline` | Allows access to the /tpoffline command | - | - |
| `essentials.tpohere` | Allows access to the /tpohere command | - | - |
| `essentials.tppos` | Allows access to the /tppos command | - | - |
| `essentials.tpr` | Allows access to the /tpr command | - | - |
| `essentials.tptoggle` | Allows access to the /tptoggle command | - | - |
| `essentials.tptoggle.others` | Allows access to the /tptoggle command for other players | - | - |
| `essentials.tree` | Allows access to the /tree command | - | - |
| `essentials.unban` | Allows access to the /unban command | - | - |
| `essentials.unbanip` | Allows access to the /unbanip command | - | - |
| `essentials.unlimited` | Allows access to the /unlimited command | - | - |
| `essentials.unlimited.item-<item-name>` | Allows access to the /unlimited command for a specific item when permission-based-item-spawn is enabled | - | - |
| `essentials.unlimited.item-all` | Allows access to the /unlimited command for all items when permission-based-item-spawn is enabled | - | - |
| `essentials.unlimited.item-bucket` | Allows access to the /unlimited command for buckets of water and lava | - | - |
| `essentials.unlimited.others` | Allows access to the /unlimited command for other players | - | - |
| `essentials.updatecheck` | The bearer will be notified of updates to EssentialsX | - | - |
| `essentials.vanish` | Allows access to the /vanish command | - | - |
| `essentials.vanish.effect` | Applies invisibility effects to the player when they are in vanish mode | - | - |
| `essentials.vanish.interact` | Allows the bearer to interact with players in vanish mode | - | - |
| `essentials.vanish.others` | Allows access to the /vanish command for other players | - | - |
| `essentials.vanish.pickup` | Allows the bearer to pick up items while in vanish mode | False | - |
| `essentials.vanish.pvp` | Allows the bearer to attack players while in vanish mode | - | - |
| `essentials.vanish.see` | Allows the bearer to see other players in vanish mode | - | - |
| `essentials.version` | Allows access to the /version command | - | - |
| `essentials.warp` | Allows access to the /warp command | - | - |
| `essentials.warp.list` | Allows access to the /warp list command | - | - |
| `essentials.warp.others` | Allows access to the /warp command for other players | - | - |
| `essentials.warp.overwrite.*` | Allows the bearer to overwrite all warps | - | - |
| `essentials.warp.overwrite.<warp-name>` | Allows the bearer to overwrite a specific warp | - | - |
| `essentials.warpinfo` | Allows access to the /warpinfo command | - | - |
| `essentials.weather` | Allows access to the /weather command | - | - |
| `essentials.whitelist.bypass` | Allows a player to join the server even if they are not whitelisted. | - | - |
| `essentials.whois` | Allows access to the /whois command | - | - |
| `essentials.whois.ip` | Allows access to the /whois command with IP address | - | - |
| `essentials.workbench` | Allows access to the /workbench command | - | - |
| `essentials.world` | Allows access to the /world command | - | - |
| `essentials.worlds.<world-name>` | Allows access to the specific world with various commands | - | - |
| `essentials.worth` | Allows access to the /worth command | - | - |

## 3. EzShops v2.5.9

- 文件：`EzShops-2.5.9.jar`（plugin.yml）
- 指令 15 个 / 权限节点 26 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `playershop` | - | Configure your player shop sign before placing it. | `ezshops.playershop.create` |
| `playershops` | - | Browse all active player shops and purchase items directly. | `ezshops.playershop.browse` |
| `price` | - | Check the shop price of a material. | `ezshops.shop` |
| `pricingadmin` | - | Admin commands for EzShops dynamic pricing | `ezshops.pricing.admin` |
| `sell` | - | Open the quick sell GUI to sell items quickly. | `ezshops.shop.sell` |
| `sellhand` | - | Sell the item currently in your hand to the shop. | `ezshops.shop.sell` |
| `sellinventory` | - | Sell all sellable items from your inventory to the shop. | `ezshops.shop.sell` |
| `setupshops` | - | Admin GUI to configure shop features | `ezshops.setupshops` |
| `shop` | - | Access the Skyblock shop to buy or sell items. | `ezshops.shop` |
| `shopadmin` | - | Admin GUI to inspect all active player shops and team market listings | `ezshops.shop.admin` |
| `signshop` | - | Configure and generate shop signs with custom backings. | `ezshops.shop.sign.setup` |
| `stock` | stk | View and manage the EzShops stock market | `ezshops.stock.view` |
| `stockadmin` | - | Admin commands for EzShops stock market | `ezshops.stock.admin` |
| `stocks` | stks | Quick overview of cached stock quotes | `ezshops.stock.view` |
| `teamshop` | - | Open the team shop dashboard (treasury, shared stocks, team market) | `ezshops.teamshop` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `ezshops.playershop.admin` | Allows administrators to manage any player shop. | op | - |
| `ezshops.playershop.browse` | Allows players to browse all player shops via /playershops. | True | - |
| `ezshops.playershop.buy` | Allows players to purchase from player shops. | True | - |
| `ezshops.playershop.create` | Allows players to create sign-based chest shops. | True | - |
| `ezshops.pricing.admin` | Admin functions for dynamic pricing (reset/resetall) | op | - |
| `ezshops.pricing.admin.disable` | Disable buying or selling for a configured item | op | - |
| `ezshops.pricing.admin.list` | List configured prices via /pricingadmin list | op | - |
| `ezshops.pricing.admin.reset` | Reset dynamic pricing for a single item | op | - |
| `ezshops.pricing.admin.resetall` | Reset all dynamic pricing entries | op | - |
| `ezshops.pricing.admin.set` | Set configured base price for an item | op | - |
| `ezshops.setupshops` | Open the shop setup GUI to enable/disable features | op | - |
| `ezshops.shop` | Allows players to access the /shop command. | True | - |
| `ezshops.shop.admin` | Open the /shopadmin moderation GUI (inspect and remove any shop or market listing) | op | - |
| `ezshops.shop.admin.minionhead` | Allows administrators to buy minion heads directly. | op | - |
| `ezshops.shop.buy` | Allows players to purchase items from the shop. | True | - |
| `ezshops.shop.sell` | Allows players to sell items to the shop. | True | - |
| `ezshops.shop.sign.create` | Allows players to create shop signs. | op | - |
| `ezshops.shop.sign.scan` | Allows players to scan and convert legacy shop signs. | op | - |
| `ezshops.shop.sign.setup` | Allows players to open the /signshop setup GUI. | op | - |
| `ezshops.stock.admin` | Admin functions for stock market | op | - |
| `ezshops.stock.refresh` | Refresh stock quotes | op | - |
| `ezshops.stock.view` | View stock quotes | True | - |
| `ezshops.teamshop` | Open the team shop (/teamshop) | True | - |
| `ezshops.teamshop.admin` | Admin override for team shop features | op | - |
| `ezshops.teamshop.market` | Access the team P2P market (list and purchase items from teammates) | True | - |
| `ezshops.teamshop.treasury.withdraw` | Withdraw from team treasury (OWNER/ADMIN role also required) | True | - |

## 4. F3F4Perms v1.3.0

- 文件：`F3F4Perms-1.3.0.jar`（plugin.yml）
- 指令 2 个 / 权限节点 4 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `f3f4perms` | - | - | `-` |
| `f3nperm` | - | - | `-` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `f3f4perms.admin` | - | op | - |
| `f3f4perms.use` | - | op | - |
| `f3nperm.admin` | - | op | - |
| `f3nperm.use` | - | op | - |

## 5. GetMeHome v3.0.0

- 文件：`GetMeHome-3.0.0-4.jar`（plugin.yml）
- 指令 6 个 / 权限节点 14 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `delhome` | - | Deletes a set home | `getmehome.command.delhome` |
| `getmehome` | - | GetMeHome's main (help) command | `-` |
| `home` | h | Sends you home | `getmehome.command.home` |
| `listhomes` | homes | Lists all the homes | `getmehome.command.listhomes` |
| `setdefaulthome` | - | Sets a different home name as the default home. | `getmehome.command.setdefaulthome` |
| `sethome` | - | Sets home at your current position | `getmehome.command.sethome` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `bstats` | Allows bStats to collect plugin metrics | True | - |
| `getmehome.command.delhome` | Allows /delhome | - | - |
| `getmehome.command.delhome.other` | Allows `/delhome <player> <name>` to delete other player's home | op | - |
| `getmehome.command.home` | Allows /home | - | - |
| `getmehome.command.home.other` | Allows `/home <player> <home>` to teleport to other user's homes | op | - |
| `getmehome.command.listhomes` | Allows /listhomes | - | - |
| `getmehome.command.listhomes.other` | Allows `/listhomes <player>` (as opposed to just /listhomes) | op | - |
| `getmehome.command.setdefaulthome` | Allows /setdefaulthome | - | - |
| `getmehome.command.sethome` | Allows /sethome | - | - |
| `getmehome.command.sethome.other` | Allows `/sethome <player> <name>` to set other player's home | op | - |
| `getmehome.delay.allowmove` | Allows moving while waiting for /home warmup | False | - |
| `getmehome.delay.instantother` | No delay for /home to other player's home | op | - |
| `getmehome.reload` | Allows /getmehome reload | op | - |
| `getmehome.user` | Allows the user-level usage of home commands | True | - |

## 6. Geyser-Spigot v2.11.2-SNAPSHOT

- 文件：`Geyser-Spigot-1233.jar`（plugin.yml）
- 指令 1 个 / 权限节点 1 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `/geyser` | - | Geyser 管理（status/version 等） | `geyser.command.*` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `geyser.command.*` | Geyser 管理命令 | op | - |

## 7. GriefPrevention v16.18.7

- 文件：`GriefPrevention.jar`（plugin.yml）
- 指令 46 个 / 权限节点 37 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `abandonallclaims` | - | Deletes ALL your claims. | `griefprevention.abandonallclaims` |
| `abandonclaim` | unclaim,declaim,removeclaim,disclaim | Deletes a claim. | `griefprevention.claims` |
| `abandontoplevelclaim` | - | Deletes a claim and all its subdivisions. | `griefprevention.claims` |
| `accesstrust` | a,t | Grants a player entry to your claim(s) and use of your bed, buttons, and levers. | `griefprevention.claims` |
| `adjustbonusclaimblocks` | a,c,b | Adds or subtracts bonus claim blocks for a player. | `griefprevention.adjustclaimblocks` |
| `adjustbonusclaimblocksall` | a,c,b,a,l,l | Adds or subtracts bonus claim blocks for all online players. | `griefprevention.adjustclaimblocks` |
| `adminclaims` | a,c | Switches the shovel tool to administrative claims mode. | `griefprevention.adminclaims` |
| `adminclaimslist` | - | Lists all administrative claims. | `griefprevention.adminclaims` |
| `basicclaims` | b,c | Switches the shovel tool back to basic claims mode. | `griefprevention.claims` |
| `buyclaimblocks` | b,u,y,c,l,a,i,m | Purchases additional claim blocks with server money.  Doesn't work on servers without a Vault-compatible economy plugin. | `griefprevention.buysellclaimblocks` |
| `claim` | createclaim,makeclaim,newclaim | Creates a land claim centered at your current location with the given radius. | `griefprevention.claims` |
| `claimbook` | - | Gives a player a manual about claiming land. | `griefprevention.claimbook` |
| `claimexplosions` | c,l,a,i,m,e,x,p,l,o,s,i,o,n | Toggles whether explosives may be used in a specific land claim. | `griefprevention.claims` |
| `claimslist` | claimlist,listclaims | Lists information about a player's claim blocks and claims. | `griefprevention.claims` |
| `containertrust` | c,t | Grants a player access to your claim's containers, crops, animals, bed, buttons, and levers. | `griefprevention.claims` |
| `deletealladminclaims` | - | Deletes all administrative claims. | `griefprevention.adminclaims` |
| `deleteallclaims` | - | Deletes all of another player's claims. | `griefprevention.deleteclaims` |
| `deleteclaim` | - | Deletes the claim you're standing in, even if it's not your claim. | `griefprevention.deleteclaims` |
| `deleteclaimsinworld` | deleteallclaimsinworld,clearclaimsinworld,clearallclaimsinworld | Deletes all the claims in a world.  Only usable at the server console. | `griefprevention.deleteclaimsinworld` |
| `deleteuserclaimsinworld` | deletealluserclaimsinworld,clearuserclaimsinworld,clearalluserclaimsinworld | Deletes all the non-admin claims in a world.  Only usable at the server console. | `griefprevention.deleteclaimsinworld` |
| `extendclaim` | expandclaim,resizeclaim | Resizes the land claim you're standing in by pushing or pulling its boundary in the direction you're facing. | `griefprevention.claims` |
| `givepet` | - | Allows a player to give away a pet he or she tamed. | `griefprevention.givepet` |
| `gpblockinfo` | - | Allows an administrator to get technical information about blocks in the world and items in hand. | `griefprevention.gpblockinfo` |
| `gpreload` | - | Reloads Grief Prevention's configuration settings.  Does NOT totally reload the entire plugin. | `griefprevention.reload` |
| `ignoreclaims` | i,c | Toggles ignore claims mode. | `griefprevention.ignoreclaims` |
| `ignoredplayerlist` | ignores,ignored,ignorelist,ignoredlist,listignores,listignored,ignoring | Lists the players you're ignoring in chat. | `griefprevention.ignore` |
| `ignoreplayer` | ignore | Ignores another player's chat messages. | `griefprevention.ignore` |
| `permissiontrust` | p,t | Grants a player permission to grant his level of permission to others. | `griefprevention.claims` |
| `restorenature` | r,n | Switches the shovel tool to restoration mode. | `griefprevention.restorenature` |
| `restorenatureaggressive` | r,n,a | Switches the shovel tool to aggressive restoration mode. | `griefprevention.restorenatureaggressive` |
| `restorenaturefill` | r,n,f | Switches the shovel tool to fill mode. | `griefprevention.restorenatureaggressive` |
| `restrictsubclaim` | r,s,c | Restricts a subclaim, so that it inherits no permissions from the parent claim | `griefprevention.claims` |
| `sellclaimblocks` | s,e,l,l,c,l,a,i,m | Sells your claim blocks for server money.  Doesn't work on servers without a Vault-compatible economy plugin. | `griefprevention.buysellclaimblocks` |
| `separate` | - | Forces two players to ignore each other in chat. | `griefprevention.separate` |
| `setaccruedclaimblocks` | s,c,b | Updates a player's accrued claim block total. | `griefprevention.adjustclaimblocks` |
| `siege` | - | Initiates a siege versus another player. | `griefprevention.siege` |
| `softmute` | - | Toggles whether a player's messages will only reach other soft-muted players. | `griefprevention.softmute` |
| `subdivideclaims` | sc,subdivideclaim | Switches the shovel tool to subdivision mode, used to subdivide your claims. | `griefprevention.claims` |
| `transferclaim` | g,i,v,e,c,l,a,i,m | Converts an administrative claim to a private claim. | `griefprevention.transferclaim` |
| `trapped` | - | Ejects you to nearby unclaimed land.  Has a substantial cooldown period. | `griefprevention.trapped` |
| `trust` | t,r | Grants a player full access to your claim(s). | `griefprevention.claims` |
| `trustlist` | - | Lists permissions for the claim you're standing in. | `griefprevention.claims` |
| `unignoreplayer` | unignore | Unignores another player's chat messages. | `griefprevention.ignore` |
| `unlockdrops` | - | Allows other players to pick up the items you dropped when you died. | `griefprevention.unlockdrops` |
| `unseparate` | - | Reverses /separate. | `griefprevention.separate` |
| `untrust` | u,t | Revokes a player's access to your claim(s). | `griefprevention.claims` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `griefprevention.abandonallclaims` | Grants access to /abandonallclaims. | True | - |
| `griefprevention.adjustclaimblocks` | Grants permission to add or remove bonus blocks from a player's account. | op | - |
| `griefprevention.admin.*` | Grants all administrative functionality. | - | - |
| `griefprevention.adminclaims` | Grants permission to create administrative claims. | op | - |
| `griefprevention.buysellclaimblocks` | Grants access to claim block buy/sell commands. | True | - |
| `griefprevention.claimbook` | Grants access to /claimbook. | op | - |
| `griefprevention.claims` | Grants access to claim-related slash commands. | True | - |
| `griefprevention.claimslistother` | Grants permission to use /claimslist to get another player's information. | op | - |
| `griefprevention.createclaims` | Grants permission to create claims. | True | - |
| `griefprevention.deleteclaims` | Grants permission to delete other players' claims. | op | - |
| `griefprevention.eavesdrop` | Allows a player to see whispered chat messages (/tell) and softmuted messages. | op | - |
| `griefprevention.eavesdropimmune` | Players with this permission can't have their private messages eavesdropped. | op | - |
| `griefprevention.eavesdropsigns` | Allows a player to see sign placements as chat messages. | op | - |
| `griefprevention.givepet` | Grants permission to use /givepet. | True | - |
| `griefprevention.gpblockinfo` | Grants access to /gpblockinfo. | op | - |
| `griefprevention.ignore` | Grants access to /ignore, /unignore, and /ignorelist | True | - |
| `griefprevention.ignoreclaims` | Grants permission to use /ignoreclaims. | op | - |
| `griefprevention.lava` | Grants permission to place lava near the surface and outside of claims. | op | - |
| `griefprevention.notignorable` | Players with this permission can't be ignored. | op | - |
| `griefprevention.overrideclaimcountlimit` | Allows players to create more claims than the limit specified by the config. | op | - |
| `griefprevention.premovementchat` | Players with this permission can chat before moving. | False | - |
| `griefprevention.reload` | Grants access to /gpreload. | op | - |
| `griefprevention.restorenature` | Grants permission to use /restorenature. | op | - |
| `griefprevention.restorenatureaggressive` | Grants access to /restorenatureaggressive and /restorenaturefill. | op | - |
| `griefprevention.seeclaimsize` | Allows a player to see claim size for other players claims when right clicking with investigation tool | op | - |
| `griefprevention.seeinactivity` | Players with this permission can see how long a claim owner has been offline. | op | - |
| `griefprevention.separate` | Grants access to /separate and /unseparate. | op | - |
| `griefprevention.siege` | Grants permission to use /siege. | True | - |
| `griefprevention.siegeimmune` | Makes a player immune to /siege. | op | - |
| `griefprevention.siegeteleport` | Players with this permission can teleport into and out of besieged areas. | op | - |
| `griefprevention.softmute` | Grants access to /softmute. | op | - |
| `griefprevention.spam` | Grants permission to log in, send messages, and send commands rapidly. | op | - |
| `griefprevention.transferclaim` | Grants permission to use /transferclaim. | op | - |
| `griefprevention.trapped` | Grants permission to use /trapped. | True | - |
| `griefprevention.unlockdrops` | Grants permission to use /unlockdrops. | True | - |
| `griefprevention.unlockothersdrops` | Grants permission to use /unlockdrops for other players. | op | - |
| `griefprevention.visualizenearbyclaims` | Allows a player to see all nearby claims at once. | op | - |

## 8. LoginSecurity v3.3.2-SNAPSHOT

- 文件：`LoginSecurity-3.3.2-SNAPSHOT.jar`（plugin.yml）
- 指令 6 个 / 权限节点 2 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `changepassword` | changepass | Change your account password. | `-` |
| `lac` | - | LoginSecurity Admin command. | `-` |
| `login` | - | Login with your account. | `-` |
| `logout` | - | Log out of your account. | `-` |
| `register` | - | Set a password for your account. | `-` |
| `unregister` | - | Unregister your account. | `-` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `ls.bypass` | Bypass registration requirement | False | - |
| `ls.update` | Notify player of available updates | op | - |

## 9. LuckPerms v5.5.81

- 文件：`LuckPerms-5.5.81.jar`（plugin.yml）
- 指令 2 个 / 权限节点 4 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `/lp` | - | 权限管理总命令（user/group/track） | `luckperms.*` |
| `luckperms` | lp,perm,perms,permission,permissions | Manage permissions | `-` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `luckperms.*` | 全部 LP 管理权限（仅 admin） | op | admin |
| `luckperms.user.demote` | 用户降级 | op | - |
| `luckperms.user.info` | 查看用户信息 | op | - |
| `luckperms.user.promote` | 用户晋升 | op | - |

## 10. OrzMC v1.0.24

- 文件：`OrzMC-1.0.24-dev.jar`（paper-plugin.yml）
- 指令 5 个 / 权限节点 4 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `/apply` | - | 申请晋升（member→builder） | `orzmc.apply` |
| `/config` | - | OrzMC 配置管理（别名 /cfg） | `orzmc.admin` |
| `/orzdebug` | - | 模拟群管理员发 Bot 命令（测试） | `orzmc.admin` |
| `/portal` | - | 跨服传送门管理 | `orzmc.admin` |
| `/review` | - | 审核申请（管理） | `orzmc.review` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `orzmc.admin` | OrzMC 管理命令 | op | admin |
| `orzmc.apply` | 提交晋升申请 | true | default |
| `orzmc.review` | 审核申请（admin 或 op） | op | admin |
| `orzmc.tpbow.use` | 使用传送弓 | true | default |

## 11. SkinsRestorer v15.12.5

- 文件：`SkinsRestorer.jar`（plugin.yml）
- 指令 3 个 / 权限节点 3 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `/skin` | - | 设置皮肤 | `skinsrestorer.command.skin` |
| `/skin clear` | - | 清除皮肤 | `skinsrestorer.command.skin` |
| `/skin set` | - | 设置皮肤 | `skinsrestorer.command.skin` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `skinsrestorer.command.skin` | 设置/清除皮肤（默认所有玩家） | true | default |
| `skinsrestorer.command.skin.clear` | 清除皮肤 | true | default |
| `skinsrestorer.command.skin.set` | 设置皮肤 | true | default |

## 12. Vault v1.7.3-b131

- 文件：`Vault.jar`（plugin.yml）
- 指令 2 个 / 权限节点 1 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `vault-convert` | - | Converts all data in economy1 and dumps it into economy2 | `vault.admin` |
| `vault-info` | - | Displays information about Vault | `vault.admin` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `vault.admin` | Notifies the player when vault is in need of an update. | op | - |

## 13. ViaBackwards v5.11.0

- 文件：`ViaBackwards-5.11.0.jar`（plugin.yml）
- 指令 0 个 / 权限节点 0 个

## 14. ViaRewind v4.1.3

- 文件：`ViaRewind-4.1.3.jar`（plugin.yml）
- 指令 0 个 / 权限节点 0 个

## 15. ViaVersion v5.11.0

- 文件：`ViaVersion-5.11.0.jar`（plugin.yml）
- 指令 2 个 / 权限节点 1 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `/viaversion` | - | ViaVersion 管理（版本兼容信息） | `viaversion.admin` |
| `viaversion` | viaver,vvbukkit | Shows ViaVersion Version and more. | `viaversion.command` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `viaversion.admin` | ViaVersion 管理 | op | - |

## 16. DeathChest v3.0.1

- 文件：`deathchest.jar`（plugin.yml）
- 指令 0 个 / 权限节点 9 个

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `deathchest.admin` | - | op | - |
| `deathchest.admin.deathchest.command.deathchest` | - | - | - |
| `deathchest.admin.deathchest.command.deleteInWorld` | - | - | - |
| `deathchest.admin.deathchest.command.reload` | - | - | - |
| `deathchest.admin.deathchest.command.report` | - | - | - |
| `deathchest.command.deleteInWorld` | The permission to delete all chests in all or a specific world | op | - |
| `deathchest.command.reload` | The permission to reload the configuration file of the DeathChest plugin | op | - |
| `deathchest.command.report` | The permission to create, read and delete reports of the plugin | op | - |
| `deathchest.update` | Notifies the player about plugin updates. | op | - |

## 17. GrimAC v2.3.74-58c8b92

- 文件：`grimac-bukkit-2.3.74.jar`（plugin.yml）
- 指令 0 个 / 权限节点 14 个

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `grim.alerts` | Receive alerts for violations | op | - |
| `grim.alerts.enable-on-join` | Enable alerts on join | op | - |
| `grim.brand` | Show client brands on join | op | - |
| `grim.brand.enable-on-join` | Enable showing client brands on join | op | - |
| `grim.disabled` | Disable Grim checks while keeping player state tracked | false | - |
| `grim.exempt` | Exempt from all checks | false | - |
| `grim.list` | Shows lists of specific data | false | - |
| `grim.nomodifypacket` | Disable modifying packets | false | - |
| `grim.nosetback` | Disable setback | false | - |
| `grim.performance` | Check performance metrics | op | - |
| `grim.profile` | Check user profile | op | - |
| `grim.sendalert` | Send cheater alert | op | - |
| `grim.verbose` | Receive verbose alerts for violations | op | - |
| `grim.verbose.enable-on-join` | Enable verbose alerts on join | false | - |

## 18. packetevents v2.13.0

- 文件：`packetevents-spigot-2.13.0.jar`（plugin.yml）
- 指令 1 个 / 权限节点 1 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `/packetevents` | - | packetevents 调试/管理 | `packetevents.*` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `packetevents.*` | packetevents 管理（内部库，正常不授予） | op | - |

## 19. voicechat v2.6.21

- 文件：`voicechat-bukkit-2.6.21.jar`（plugin.yml）
- 指令 1 个 / 权限节点 4 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `voicechat` | - | Manage voice chat | `-` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `voicechat.admin` | Allows to test voice chat connections | - | - |
| `voicechat.groups` | Allows to join groups | - | - |
| `voicechat.listen` | Allows to listen to voice chat | - | - |
| `voicechat.speak` | Allows to speak in voice chat | - | - |

## 20. WorldEdit v7.4.5+7590-b8dc4c1

- 文件：`worldedit-bukkit-7.4.5.jar`（plugin.yml）
- 指令 19 个 / 权限节点 17 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `//brush` | - | 设置笔刷 | `worldedit.brush.*` |
| `//contract` | - | 收缩选区 | `worldedit.selection.contract` |
| `//copy` | - | 复制选区到剪贴板 | `worldedit.clipboard.copy` |
| `//count` | - | 统计方块 | `worldedit.analysis.count` |
| `//expand` | - | 扩展选区 | `worldedit.selection.expand` |
| `//fill` | - | 填充 | `worldedit.region.fill` |
| `//gmask` | - | 全局遮罩 | `worldedit.global-mask` |
| `//limit` | - | 查看/设置单次编辑方块上限 | `worldedit.limit` |
| `//paste` | - | 粘贴剪贴板 | `worldedit.clipboard.paste` |
| `//pos1` | - | 设置选区点1 | `worldedit.selection.pos` |
| `//pos2` | - | 设置选区点2 | `worldedit.selection.pos` |
| `//redo` | - | 重做 | `worldedit.history.redo` |
| `//replace` | - | 替换方块 | `worldedit.region.replace` |
| `//schem` | - | 原理图保存/加载/粘贴 | `worldedit.schematic.*` |
| `//set` | - | 填充选区 | `worldedit.region.set` |
| `//tool` | - | 绑定工具 | `worldedit.tool.*` |
| `//undo` | - | 撤销上次编辑 | `worldedit.history.undo` |
| `//unstuck` | - | 脱困（当前命令未注册） | `worldedit.navigation.unstuck` |
| `//wand` | - | 获取木斧选区工具 | `worldedit.wand` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `worldedit.analysis.*` | 分析统计 | op | builder |
| `worldedit.brush.*` | 笔刷 | op | builder |
| `worldedit.clipboard.*` | 剪贴板（copy/paste） | op | builder |
| `worldedit.global-mask` | 全局遮罩 | op | - |
| `worldedit.history.*` | 历史（undo/redo） | op | builder |
| `worldedit.limit` | 查看/设置编辑上限 | op | - |
| `worldedit.navigation.*` | 导航（unstuck 未注册） | op | builder |
| `worldedit.region.*` | 区域操作（set/replace/fill 等） | op | builder |
| `worldedit.region.set` | 填充选区 | op | builder |
| `worldedit.reload` | 重载配置（管理） | op | - |
| `worldedit.schematic.*` | 原理图 | op | builder |
| `worldedit.selection.*` | 选区操作（pos1/pos2/expand 等） | op | builder |
| `worldedit.selection.pos` | 设置选区点 | op | builder |
| `worldedit.setnbt` | 设置方块实体 NBT（容器/告示牌内容） | op | - |
| `worldedit.tool.*` | 工具绑定 | op | builder |
| `worldedit.utility.*` | 实用命令（fill/drain） | op | builder |
| `worldedit.wand` | 使用木斧 | op | builder |

## 21. WorldGuard v7.0.18+2392-fa605e6

- 文件：`worldguard-bukkit-7.0.18.jar`（plugin.yml）
- 指令 7 个 / 权限节点 8 个

### 指令

| 指令 | 别名 | 用途 | 所需权限 |
|:--|:--|:--|:--|
| `//claim` | - | 选区圈地 | `worldguard.region.claim` |
| `/rg` | - | 领地管理（create/claim/define 等） | `worldguard.region.*` |
| `/rg addmember` | - | 添加成员 | `worldguard.region.addmember` |
| `/rg flag` | - | 设置领地标志 | `worldguard.region.flag.flag` |
| `/rg info` | - | 查看领地信息 | `worldguard.region.info` |
| `/rg list` | - | 列出领地 | `worldguard.region.list` |
| `/rg removemember` | - | 移除成员 | `worldguard.region.removemember` |

### 权限节点

| 权限节点 | 描述 | 默认 | 组分配 |
|:--|:--|:--|:--|
| `worldguard.region.addmember` | 添加成员 | op | - |
| `worldguard.region.bypass` | 绕过领地保护（管理，任何组不授） | op | - |
| `worldguard.region.claim` | 圈地 | op | builder |
| `worldguard.region.flag.*` | 全部领地标志（管理） | op | - |
| `worldguard.region.flag.flag` | 设置领地标志 | op | - |
| `worldguard.region.info` | 查看领地信息 | op | builder |
| `worldguard.region.list` | 列出领地 | op | builder |
| `worldguard.region.removemember` | 移除成员 | op | - |
