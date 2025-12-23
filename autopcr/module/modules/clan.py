from ..modulebase import *
from ..config import *
from ...core.pcrclient import pcrclient
from ...core.apiclient import apiclient
from ...model.error import *
from ...model.enums import *
from ...db.database import db
import random

@description('看看你是否掉刀')
@name("公会战刀数")
@default(True)
@tag_stamina_get
class clan_battle_knive(Module):
    async def do_task(self, client: pcrclient):
        top = await client.clan_battle_top()
        carry_over_count = len(top.carry_over) if top.carry_over else 0
        if not top.remaining_count and top.point == 900 and carry_over_count == 0:
            self._log("今日三刀已出完！")
        else:
            status_parts = []
            if top.remaining_count:
                status_parts.append(f"剩余整刀：{top.remaining_count}")

            time_list = [record.time for record in (top.carry_over or []) if record.time is not None and record.time > 0]
            if time_list:
                time_str = "、".join(f"{t}秒" for t in time_list)
                count = len(time_list)
                status_parts.append(f"剩余尾刀：{count}（{time_str}）")
            status_parts.append(f"体力点数：{top.point}")
            self._warn(" | ".join(status_parts))

@description('在公会中自动随机选择一位成员点赞。')
@name("公会点赞")
@default(True)
@tag_stamina_get
class clan_like(Module):
    async def do_task(self, client: pcrclient):
        if client.data.clan_like_count:
            raise SkipError('今日点赞次数已用完。')
        clan = await client.get_clan_info()
        info = clan.clan
        members = [(x.viewer_id, x.name) for x in info.members if x.viewer_id != client.viewer_id]
        if len(members) == 0: raise AbortError("nobody's home?")
        rnd = random.choice(members)
        await client.clan_like(rnd[0])
        self._log(f"为【{rnd[1]}】点赞")

@description('对某颜色缺口数量最多的装备发起请求')
@name("装备请求")
@singlechoice("clan_equip_request_color", "装备颜色", "all", ["all", "Silver", "Gold", "Purple", 'Red', 'Green'])
@singlechoice("clan_equip_request_consider_unit_rank", "起始品级", "所有", ["所有", '最高', '次高', '次次高'])
@booltype("clan_equip_request_consider_unit_fav", "收藏角色", False)
@default(False)
class clan_equip_request(Module):
    color_to_promotion = {
            'all': 0,
            "Brozen": 2,
            "Silver": 3,
            "Gold": 4,
            "Purple": 5,
            "Red": 6,
            "Green": 7,
    }
    async def do_task(self, client: pcrclient):
        clan = await client.get_clan_info()

        if clan.latest_request_time and apiclient.time <= clan.latest_request_time + client.data.settings.clan.equipment_request_interval:
            raise SkipError("当前请求尚未结束")
        elif clan.latest_request_time:
            res = await client.equip_get_request(0)
            msg = f"收到{db.get_equip_name(res.request.equip_id)}x{res.request.donation_num}：" + ' '.join(f"{user.name}x{user.num}" for user in res.request.history)
            self._log(msg.strip("："))

        opt: Dict[Union[int, str], int] = {
            '所有': 1,
            '最高': db.equip_max_rank,
            '次高': db.equip_max_rank - 1,
            '次次高': db.equip_max_rank - 2,
        }

        fav: bool = self.get_config('clan_equip_request_consider_unit_fav')
        start_rank: int = opt[self.get_config('clan_equip_request_consider_unit_rank')]
        demand = client.data.get_equip_demand_gap(like_unit_only=fav, start_rank=start_rank)
        config_color: str = self.get_config('clan_equip_request_color')
        target_level = self.color_to_promotion[config_color]

        consider_equip = [(equip_id, num) for (item_type, equip_id), num in demand.items() if 
                          db.equip_data[equip_id].enable_donation and 
                          db.equip_data[equip_id].require_level <= client.data.team_level and
                          (db.equip_data[equip_id].promotion_level == target_level or config_color == 'all')]
        consider_equip = sorted(consider_equip, key=lambda x: x[1], reverse=True)

        if consider_equip:
            (equip_id, num) = consider_equip[0]
            await client.request_equip(equip_id, clan.clan.detail.clan_id)
            self._log(f"请求【{db.get_equip_name(equip_id)}】装备，缺口数量为{num}")
        else:
            raise AbortError("没有可请求的装备")


@description('查看当前公会成员列表')
@name("公会成员列表")
@default(False)
class clan_member_list(Module):
    async def do_task(self, client: pcrclient):
        clan_info = await client.get_clan_info()
        members = getattr(getattr(clan_info, 'clan', None), 'members', [])
        if not members:
            self._log("未获取到成员信息")
            return

        members = sorted(
            members,
            key=lambda m: (-getattr(m, 'total_power', 0), getattr(m, 'viewer_id', 0))
        )
        self._log(f"成员数量：{len(members)}")
        for idx, member in enumerate(members, 1):
            name = getattr(member, 'name', '未知')
            viewer_id = getattr(member, 'viewer_id', 0)
            level = getattr(member, 'level', 0)
            power = getattr(member, 'total_power', 0)
            role = getattr(member, 'clan_role', None)
            role_name = ""
            if role is not None:
                try:
                    role_name = eClanRole(role).name
                except Exception:
                    role_name = str(role)
            line = f"{idx}. {name}({viewer_id}) Lv{level} 战力:{power}"
            if role_name:
                line += f" [{role_name}]"
            self._log(line)


@description('邀请指定玩家加入公会')
@name("邀请入会")
@texttype("target_viewer_id", "目标玩家ID", "")
@default(False)
class clan_invite_player(Module):
    async def do_task(self, client: pcrclient):
        target_viewer_id = self.get_config('target_viewer_id')
        if not target_viewer_id:
            raise AbortError("未指定目标玩家ID")
        
        try:
            target_viewer_id = int(target_viewer_id)
        except ValueError:
            raise AbortError("玩家ID必须是数字")
        
        await client.invite_to_clan(target_viewer_id,"爱你哦")
        self._log(f"已向玩家 {target_viewer_id} 发送公会邀请")



@description('快速踢出公会')
@name("踢出公会")
@texttype("target_viewer_id", "目标玩家ID", "")
@default(False)
class clan_kick_player(Module):
    async def do_task(self, client: pcrclient):
        target_viewer_id = self.get_config('target_viewer_id')
        if not target_viewer_id:
            raise AbortError("未指定目标玩家ID")
        
        try:
            target_viewer_id = int(target_viewer_id)
        except ValueError:
            raise AbortError("玩家ID必须是数字")
        
        await client.remove_member(target_viewer_id)
        self._log(f"已踢出 {target_viewer_id} ")