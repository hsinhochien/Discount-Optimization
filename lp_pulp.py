# pip install pulp==2.9.0

from pulp import LpMaximize, LpProblem, LpVariable, lpSum, LpBinary, value, PULP_CBC_CMD
from get_input import get_input
import math
from collections import Counter

def get_optimal_discount(input_dict):
    paras = get_input(input_dict)
    products = paras['products']
    products_qty = paras['products_qty']
    products_set_qty = paras['products_set_qty']
    products_set = paras['products_set']
    discounts = paras['discounts']
    discount_limits = paras['discount_limits']
    discount_thresholds = paras['discount_thresholds']
    discount_able = paras['discount_able']
    discount_type = paras['discount_type']
    
    # 創建模型
    model = LpProblem("discount_optimization", LpMaximize)
    
    # 定義變量
    x = {}  # x[i,d] 表示商品組合 i 是否使用折扣 d
    z = {}  # z[i] 表示商品組合 i 是否被使用
    
    for i in products:
        z[i] = LpVariable(f"z_{i}", cat=LpBinary)
        set_pid = products_set[i]
        for d in discounts:
            # set裡面的都要可以用券
            discount_ok = True
            for pid in set_pid:
                discount_list = discount_able[pid]
                if d not in discount_list:
                    discount_ok = False
                    break
            if discount_ok:
                # 要符合threshold
                if discount_type[d] == 'A':
                    if products[i] >= discount_thresholds[d]:
                        x[(i,d)] = LpVariable(f"x_{i}_{d}", cat=LpBinary)
                elif discount_type[d] == 'Q':
                    if products_set_qty[i] >= discount_thresholds[d]:
                        x[(i,d)] = LpVariable(f"x_{i}_{d}", cat=LpBinary)
                    
    # 新增變量: y[d] 表示是否達到折扣 d 的門檻
    y = {d: LpVariable(f"y_{d}", cat=LpBinary) for d in discounts}
    
    # 添加約束條件
    # 每個商品組合最多使用一個折扣碼
    for i in products:
        model += lpSum(x[(i,d)] for d in discounts if (i,d) in x) <= z[i]
    
    # 確保每個商品只出現在一個組合中
    all_pids = set()
    for pids in products_set.values():
        all_pids.update(pids)
    
    for pid in all_pids:
        model += lpSum(z[i] for i, pids in products_set.items() if pid in pids) <= 1
    
    # 折扣碼使用次數限制
    for d in discounts:
        model += lpSum(x[(i,d)] for i in products if (i,d) in x) <= discount_limits[d]
    
    # 折扣門檻限制
    for d in discounts:
        model += lpSum(x[(i,d)] * products[i] for i in products if (i,d) in x) >= discount_thresholds[d] * y[d]
        model += y[d] <= lpSum(x[(i,d)] for i in products if (i,d) in x)
    
    # 定義目標函數：根據折扣金額是否大於等於 1 來選擇計算方式
    objective_terms = []
    for i in products:
        for d in discounts:
            if (i, d) in x:
                is_BC = d[0:2] == 'BC'
                if discounts[d] >= 1:
                    if is_BC:
                        objective_terms.append(x[(i, d)] * discounts[d] * products_set_qty[i])
                    else:
                        objective_terms.append(x[(i, d)] * discounts[d])
                else:
                    objective_terms.append(x[(i, d)] * (1 - discounts[d]) * products[i])
    
    model += lpSum(objective_terms)
    
    # 求解
    model.solve(PULP_CBC_CMD(msg=False))
    
    # 整理輸出
    total_discount = 0
    campaigns_result = []
    selected_discount_list = []
    campaigns_result_final = []
    if model.status == 1:
        for i in products:
            if value(z[i]) > 0.5:
                for d in discounts:
                    is_BC = d[0:2] == 'BC'
                    if (i,d) in x and value(x[(i,d)]) > 0.5:
                        if discounts[d] >= 1:
                            if is_BC:
                                discount_value = products_set_qty[i] * discounts[d]
                            else:
                                discount_value = discounts[d]
                        else:
                            discount_value = (1-discounts[d])*products[i]
                        discount_value = math.ceil(discount_value) #無條件進位
                        total_discount += discount_value
                        temp_dict = {
                            "campaignId": d,
                            "discount": discount_value,
                            "items": products_set[i]
                            }
                        selected_discount_list.append(temp_dict)
           
        # 組合同樣的折扣碼
        merged_dict = {}
        for d in selected_discount_list:
            campaign_id = d["campaignId"]
            
            if campaign_id not in merged_dict:
                merged_dict[campaign_id] = {
                    "campaignId": campaign_id,
                    "discount": 0,
                    "items": [],
                    "pids": []
                }
            
            # 合併折扣
            merged_dict[campaign_id]["discount"] += d["discount"]
            
            # 合併項目
            temp_items = merged_dict[campaign_id]["items"]
            for pid in d['items']:
                temp_items.extend([pid]*products_qty[pid])
            merged_dict[campaign_id]["items"] = temp_items
            
        # 轉換成列表格式
        campaigns_result = list(merged_dict.values())
        
        # 整合items
        for dict_sub in campaigns_result:
            ori_items = dict_sub['items']
            new_items = dict(Counter(ori_items))
            unique_items = list(set(ori_items))
            items_list = [{"pid": pid, "qty": qty} for pid, qty in new_items.items()]
            dict_sub['items'] = items_list
            dict_sub['pids'] = unique_items
            campaigns_result_final.append(dict_sub)

    result_dict = {
        "resultData": {
             "campaigns": campaigns_result_final,
             "totalDiscount": total_discount           
            }
    }
    return result_dict


input_dict_1 = {
    "comboDiscounts": [
        {
            "campaignId": "BC_240801145409145",
            "discounts": {
                "A": [499, 50]},
            "items": [
                {"pid": 2056401, "price": 680, "qty": 1},
                {"pid": 1013018, "price": 790, "qty": 10}
            ]
        },
        {
            "campaignId": "CD_240731110049539",
            "discounts": {"A": [500,0.8]},
            "items": [
                {"pid": 2056401, "price": 680, "qty": 1}
            ]
        }
    ]
}

input_dict_2 = {
    "comboDiscounts": [
        {
            "campaignId": "campaign11_best",
            "discounts": {"A": [1000,0.85]},
            "items": [
                {"pid": 101, "price": 1000, "qty": 2},
                {"pid": 102, "price": 1001, "qty": 1},
                {"pid": 103, "price": 1000, "qty": 3}
            ]
        },
        {
            "campaignId": "campaign12",
            "discounts": {"A": [1000,0.95]},
            "items": [
                {"pid": 101, "price": 1000, "qty": 2},
                {"pid": 102, "price": 1001, "qty": 1},
                {"pid": 103, "price": 1000, "qty": 3}
            ]
        },
        {
            "campaignId": "campaign13",
            "discounts": {"A": [1000,0.9]},
            "items": [
                {"pid": 101, "price": 1000, "qty": 2},
                {"pid": 102, "price": 1001, "qty": 1},
                {"pid": 103, "price": 1000, "qty": 3}
            ]
        },
        {
            "campaignId": "campaign21",
            "discounts": {"A": [1000,0.9]},
            "items": [
                {"pid": 104, "price": 1000, "qty": 2},
                {"pid": 105, "price": 1001, "qty": 1},
                {"pid": 106, "price": 1000, "qty": 3}
            ]
        },
        {
            "campaignId": "campaign22_best",
            "discounts": {"A": [1000,0.85]},
            "items": [
                {"pid": 104, "price": 1000, "qty": 2},
                {"pid": 105, "price": 1001, "qty": 1},
                {"pid": 106, "price": 1000, "qty": 3}
            ]
        },
        {
            "campaignId": "campaign23",
            "discounts": {"A": [1000,0.95]},
            "items": [
                {"pid": 104, "price": 1000, "qty": 2},
                {"pid": 105, "price": 1001, "qty": 1},
                {"pid": 106, "price": 1000, "qty": 3}
            ]
        },
        {
            "campaignId": "campaign31",
            "discounts": {"A": [1000,0.95]},
            "items": [
                {"pid": 107, "price": 1000, "qty": 2},
                {"pid": 108, "price": 1001, "qty": 1},
                {"pid": 109, "price": 1000, "qty": 3}
            ]
        },
        {
            "campaignId": "campaign32",
            "discounts": {"A": [1000,0.9]},
            "items": [
                {"pid": 107, "price": 1000, "qty": 2},
                {"pid": 108, "price": 1001, "qty": 1},
                {"pid": 109, "price": 1000, "qty": 3}
            ]
        },
        {
            "campaignId": "campaign33_best",
            "discounts": {"A": [1000,0.85]},
            "items": [
                {"pid": 107, "price": 1000, "qty": 2},
                {"pid": 108, "price": 1001, "qty": 1},
                {"pid": 109, "price": 1000, "qty": 3}
            ]
        },
        {
            "campaignId": "campaign41",
            "discounts": {"A": [1000,0.85]},
            "items": [
                {"pid": 101, "price": 1000, "qty": 2},
                {"pid": 105, "price": 1001, "qty": 1},
                {"pid": 108, "price": 1001, "qty": 1}
            ]
        },
        {
            "campaignId": "campaign42",
            "discounts": {"A": [1000,0.95]},
            "items": [
                {"pid": 101, "price": 1000, "qty": 2},
                {"pid": 105, "price": 1001, "qty": 1},
                {"pid": 108, "price": 1001, "qty": 1}
            ]
        },
        {
            "campaignId": "campaign43",
            "discounts": {"A": [1000,0.9]},
            "items": [
                {"pid": 101, "price": 1000, "qty": 2},
                {"pid": 105, "price": 1001, "qty": 1},
                {"pid": 108, "price": 1001, "qty": 1}
            ]
        }
    ]
}


print(get_optimal_discount(input_dict_1))
print(get_optimal_discount(input_dict_2))