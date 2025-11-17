from ..modulebase import *  
from ..config import *  
from ...core.pcrclient import pcrclient  
from ...model.requests import FriendAcceptRequest, FriendRequestRequest, FriendRemoveRequest, FriendFriendListRequest, FriendPendingListRequest  
from ...core.apiclient import ApiException  

  
@description('向指定玩家发送好友请求')  
@name("添加好友")  
@texttype("target_viewer_id", "目标玩家ID", "")
@default(False)  
class request_friend(Module):  
    async def do_task(self, client: pcrclient):  
        target_viewer_id = self.get_config('target_viewer_id')  
        if not target_viewer_id:  
            raise AbortError("未指定目标玩家ID")  
          
        try:  
            req = FriendRequestRequest()  
            req.target_viewer_id = target_viewer_id  
            await client.request(req)  
            self._log(f"已向玩家 {target_viewer_id} 发送好友请求")  
        except ApiException as e:  
            error_msg = str(e)  
              
            # 如果对方已经发送了申请,自动同意  
            if "已收到该玩家的好友申请" in error_msg:    
                accept_req = FriendAcceptRequest()  
                accept_req.target_viewer_id = target_viewer_id  
                await client.request(accept_req)  
                self._log(f"被添加，已同意玩家 {target_viewer_id} 的好友申请")  
              
  
@description('查看好友列表')  
@name("好友列表")  
@default(False)  
class friend_list(Module):  
    async def do_task(self, client: pcrclient):  
        req = FriendFriendListRequest()  
        resp = await client.request(req)  
          
        if not resp.friend_list:  
            self._log("好友列表为空")  
            return  
          
        self._log(f"好友数量: {len(resp.friend_list)}")  
        for friend in resp.friend_list:  
            self._log(f"ID: {friend.viewer_id}, 名称: {friend.name}, 等级: {friend.level}, 战力: {friend.total_power}")  
  
@description('删除指定好友')  
@name("删除好友")  
@texttype("target_viewer_id", "目标玩家ID", "")
@default(False)  
class remove_friend(Module):  
    async def do_task(self, client: pcrclient):  
        target_viewer_id = self.get_config('target_viewer_id')  
        if not target_viewer_id:  
            raise AbortError("未指定目标玩家ID")  
          
        req = FriendRemoveRequest()  
        req.target_viewer_id = target_viewer_id  
        await client.request(req)  
        self._log(f"已删除好友 {target_viewer_id}")  
  
@description('查看待处理的好友申请列表')  
@name("申请列表")  
@default(False)  
class pending_list(Module):  
    async def do_task(self, client: pcrclient):  
        req = FriendPendingListRequest()  
        resp = await client.request(req)  
          
        if not resp.pending_list:  
            self._log("没有待处理的好友申请")  
            return  
          
        self._log(f"待处理申请数量: {len(resp.pending_list)}")  
        for pending in resp.pending_list:  
            self._log(f"ID: {pending.viewer_id}, 名称: {pending.name}, 等级: {pending.level}, 战力: {pending.total_power}")