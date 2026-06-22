"""
Foundation Kernel (NG+F Reference Implementation)
組織を実行可能な状態機械（State Machine）として扱う最小カーネル。
理念・定款・ガバナンスをイベント駆動で処理し、ミッション・ドリフト（理念逸脱）を監視します。
"""

import copy
import time

# ============================================================
# 【SECTION 1: STATE MODEL】
# ============================================================
class HierarchicalMission:
    """理念を4つの階層に分類して管理するクラス"""
    def __init__(self, large="", medium=None, small=None, method=None):
        self.large = large  # 大項目：究極の目的（変更は一発アウト）
        self.medium = medium if medium else []  # 中項目：具体的アプローチ/事業領域
        self.small = small if small else []    # 小項目：行動指針やルール
        self.method = method if method else []  # 手法：具体的な手段のリスト

class OrganizationState:
    """組織の現在の状態を保持するクラス"""
    def __init__(self):
        self.name = ""
        self.mission = HierarchicalMission()
        self.members = {}  # {id: role}
        self.assets = {"foundation_funds": 0.0}
        self.min_funds = 1000.0
        self.proposals = {}
        self.history = []
        self.mission_drift = 0.0
        self.is_locked = False
        self.org_id = "FOUNDATION-ORIGIN"
        self.parent_id = None
        self.fork_count = 0
        self.generation = 1
        self.version = 0
        self.org_type = "STANDARD"

# ============================================================
# 【SECTION 2: EVENT MODEL】
# ============================================================
class Event:
    """組織に発生する変更や意思決定を記録するイベントオブジェクト"""
    def __init__(self, type, payload, author):
        self.type = type
        self.payload = payload
        self.author = author
        self.timestamp = time.time()

# ============================================================
# 【SECTION 3: KERNEL CORE】
# ============================================================
class FoundationKernel:
    """組織運営のルールを強制（Enforce）するカーネル"""
    def __init__(self):
        self.state = OrganizationState()

    def emit(self, event):
        if self.state.is_locked:
            raise Exception("ORGANIZATION_LOCKED: 大項目が侵害されたため組織は凍結されています。")
        self.validate(event)
        self.apply(event)
        self.state.history.append(event)

    def validate(self, event):
        # 権限チェック
        if self.state.members.get(event.author) != "board":
            raise Exception("NOT_AUTHORIZED")

        # 理念変更のバリデーションルール
        if event.type == "update_mission":
            target_layer = event.payload.get("layer")
            action = event.payload.get("action")

            # 1. 大項目の変更は一発アウト（セーフティ）
            if target_layer == "large":
                self.state.is_locked = True
                self.state.mission_drift = 1.0
                raise Exception("CRITICAL_VIOLATION: 大項目の変更は禁止されています。")

            # 2. 中項目の変更ルール（余剰基金のチェック）
            if target_layer == "medium":
                surplus_funds = self.state.assets["foundation_funds"] - self.state.min_funds
                if action in ["edit", "delete"] and surplus_funds <= 0:
                    raise Exception("INSUFFICIENT_SURPLUS_FUNDS: 余剰基金がありません。")

    def apply(self, event):
        if event.type == "update_mission":
            layer = event.payload["layer"]
            action = event.payload["action"]
            value = event.payload["value"]
            drift_penalty = 0.0

            if layer == "medium":
                if action == "add":
                    self.state.mission.medium.append(value)
                elif action == "edit":
                    idx = event.payload["index"]
                    self.state.mission.medium[idx] = value
                    drift_penalty = 0.25
                elif action == "delete":
                    idx = event.payload["index"]
                    self.state.mission.medium.pop(idx)
                    drift_penalty = 0.3
            elif layer == "small":
                if action == "add": self.state.mission.small.append(value)
                elif action == "edit":
                    idx = event.payload["index"]
                    self.state.mission.small[idx] = value
                    drift_penalty = 0.1
            elif layer == "method":
                if action == "add": self.state.mission.method.append(value)
                # 手法(method)の変更はドリフトとしてカウントしない
            
            self.state.mission_drift = min(1.0, self.state.mission_drift + drift_penalty)
            self.state.version += 1

        if event.type == "add_member":
            self.state.members[event.payload["id"]] = event.payload["role"]

# ============================================================
# 【SECTION 4: SYSTEM CALLS & UTILITIES】
# ============================================================
def deploy_method_foundation(kernel, user, method_index, initial_grant_funds):
    """特定の手法に特化した新しい組織（手法財団）を切り出す"""
    if kernel.state.members.get(user) != "board": raise Exception("NOT_AUTHORIZED")
    if kernel.state.assets["foundation_funds"] < initial_grant_funds: raise Exception("INSUFFICIENT_FUNDS")

    kernel.state.assets["foundation_funds"] -= initial_grant_funds
    method_kernel = FoundationKernel()
    target_method = kernel.state.mission.method[method_index]

    method_kernel.state.name = f"手法財団 ({target_method} 遂行専門機関)"
    method_kernel.state.org_type = "METHOD_SPECIFIC"
    method_kernel.state.mission.large = f"【手法完遂命令】手法『{target_method}』を全うすること。"
    method_kernel.state.assets["foundation_funds"] = initial_grant_funds
    method_kernel.state.members = copy.deepcopy(kernel.state.members)
    method_kernel.state.parent_id = kernel.state.org_id
    method_kernel.state.generation = kernel.state.generation + 1

    return method_kernel

def evaluate_drift(kernel):
    print(f"\n--- 診断レポート (ID: {kernel.state.org_id}) ---")
    print(f"理念逸脱度 (Mission Drift): {kernel.state.mission_drift:.2f}")
    if kernel.state.mission_drift > 0.3:
        print("WARNING: 逸脱を検知。別法人の【フォーク】を推奨します。")

# ============================================================
# 【SECTION 5: EXECUTION EXAMPLE（実行デモ）】
# ============================================================
if __name__ == "__main__":
    # 初期セットアップ
    kernel = FoundationKernel()
    kernel.state.members["alice"] = "board"
    kernel.state.assets["foundation_funds"] = 5000.0
    
    kernel.state.mission.large = "人類が長期目標を維持できる組織の設計原理の解明"
    kernel.state.mission.medium = ["ガバナンス工学の確立","制度進化学の研究"]
    kernel.state.mission.small = ["研究成果のオープンソース化", "実証実験の実施"]
    kernel.state.mission.method = ["定款データベースの構築", "GitHubによる定款管理"]

    print("=== NG+F Kernel Booted ===")
    print("大項目:", kernel.state.mission.large)

    # 1. 手法の追加
    kernel.emit(Event("update_mission", {"layer": "method", "action": "add", "value": "定款分析AI"}, "alice"))
    
    # 2. 手法財団の切り出し
    print("\n[Action] 手法財団をデプロイします...")
    method_foundation = deploy_method_foundation(kernel, "alice", 0, 1500.0)
    print("新組織の大項目:", method_foundation.state.mission.large)

    # 3. 診断
    evaluate_drift(kernel)