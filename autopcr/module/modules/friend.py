from ..config import texttype
from ..modulebase import AbortError, Module, default, description, name
from ...core.apiclient import ApiException
from ...core.pcrclient import pcrclient
from ...model.requests import (
    FriendAcceptRequest,
    FriendFriendListRequest,
    FriendPendingListRequest,
    FriendRemoveRequest,
    FriendRequestRequest,
)


def _viewer_id(module: Module) -> int:
    value = module.get_config("target_viewer_id")
    try:
        viewer_id = int(value)
    except (TypeError, ValueError):
        raise AbortError("玩家ID必须是数字")
    if viewer_id <= 0:
        raise AbortError("未指定目标玩家ID")
    return viewer_id


@description("同意指定玩家的好友申请")
@name("同意好友")
@texttype("target_viewer_id", "目标玩家ID", "")
@default(False)
class accept_friend(Module):
    async def do_task(self, client: pcrclient):
        viewer_id = _viewer_id(self)
        request = FriendAcceptRequest()
        request.target_viewer_id = viewer_id
        await client.request(request)
        self._log(f"已同意玩家 {viewer_id} 的好友申请")


@description("向指定玩家发送好友请求；若对方已申请，则自动同意")
@name("添加好友")
@texttype("target_viewer_id", "目标玩家ID", "")
@default(False)
class request_friend(Module):
    async def do_task(self, client: pcrclient):
        viewer_id = _viewer_id(self)
        request = FriendRequestRequest()
        request.target_viewer_id = viewer_id
        try:
            await client.request(request)
            self._log(f"已向玩家 {viewer_id} 发送好友请求")
        except ApiException as exc:
            if "已收到该玩家的好友申请" not in str(exc):
                raise
            accept = FriendAcceptRequest()
            accept.target_viewer_id = viewer_id
            await client.request(accept)
            self._log(f"已同意玩家 {viewer_id} 的好友申请")


@description("查看好友列表")
@name("好友列表")
@default(False)
class friend_list(Module):
    async def do_task(self, client: pcrclient):
        response = await client.request(FriendFriendListRequest())
        friends = response.friend_list or []
        if not friends:
            self._log("好友列表为空")
            return
        self._log(f"好友数量：{len(friends)}")
        for friend in friends:
            self._log(
                f"ID：{friend.viewer_id}，名称：{friend.name}，"
                f"等级：{friend.level}，战力：{friend.total_power}"
            )


@description("删除指定好友")
@name("删除好友")
@texttype("target_viewer_id", "目标玩家ID", "")
@default(False)
class remove_friend(Module):
    async def do_task(self, client: pcrclient):
        viewer_id = _viewer_id(self)
        request = FriendRemoveRequest()
        request.target_viewer_id = viewer_id
        await client.request(request)
        self._log(f"已删除好友 {viewer_id}")


@description("查看待处理的好友申请列表")
@name("申请列表")
@default(False)
class pending_list(Module):
    async def do_task(self, client: pcrclient):
        response = await client.request(FriendPendingListRequest())
        pending = response.pending_list or []
        if not pending:
            self._log("没有待处理的好友申请")
            return
        self._log(f"待处理申请数量：{len(pending)}")
        for applicant in pending:
            self._log(
                f"ID：{applicant.viewer_id}，名称：{applicant.name}，"
                f"等级：{applicant.level}，战力：{applicant.total_power}"
            )
