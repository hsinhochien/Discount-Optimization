def get_input(input_dict): 
    products = {}
    products_qty = {}
    products_price = {}
    products_set_qty = {}
    products_set = {}
    products_set_items = set()
    discounts = {}
    discount_limits = {}
    discount_thresholds = {}
    discount_type = {}
    discount_able = {}

    combo_discounts = input_dict["comboDiscounts"]
    
    ## 折價券
    for combo in combo_discounts:
        campaign_id = combo["campaignId"]
        if 'A' in combo["discounts"]:
            discount_value = combo["discounts"]["A"][1]
            discount_threshold = combo["discounts"]["A"][0]
            d_type = 'A'
        elif 'Q' in combo["discounts"]:
            discount_value = combo["discounts"]["Q"][1]
            discount_threshold = combo["discounts"]["Q"][0]
            d_type = 'Q'
        usage_limit = 9999 if campaign_id[0:2] == 'BC' else 1
        items = combo["items"]

        # 更新折扣相關資訊
        discounts[campaign_id] = float(discount_value)
        discount_limits[campaign_id] = int(usage_limit)
        discount_thresholds[campaign_id] = float(discount_threshold)
        discount_type[campaign_id] = d_type

        # 更新商品可用的折扣碼
        for item in items:
            pid = item['pid']
            if pid not in discount_able:
                discount_able[pid] = []
            if campaign_id not in discount_able[pid]:
                discount_able[pid].append(campaign_id)
    
    ## 商品
    # 所有items
    all_items = []
    for combo in combo_discounts:
        all_items.extend(combo['items'])
    unique_items = {tuple(item.items()) for item in all_items}
    all_items = [dict(item) for item in unique_items]
    
    # 每個item可用數量
    for item in all_items:
        products_qty[item['pid']] = item['qty']
        products_price[item['pid']] = item['price']
    
    set_i = 0
    for combo in combo_discounts:
        items = combo["items"]        
        # 生成商品組合及其價格
        for i in range(1, 1 << len(items)):  # 從1到(2^n)-1, 生成所有非空子集
            selected_items = [items[j] for j in range(len(items)) if i & (1 << j)]
            set_pids = [item['pid'] for item in selected_items]
            set_pids_str = str(set(set_pids))
            if set_pids_str not in products_set_items:
                products_set_items.add(set_pids_str)
                
                set_name = f'set_{set_i + 1}'
                total_price = sum(item['price']*item['qty'] for item in selected_items)
                products[set_name] = total_price
                products_set[set_name] = set_pids
                
                total_qty = sum(item['qty'] for item in selected_items)
                products_set_qty[set_name] = total_qty
                
                set_i += 1

    return {
        'products': products,
        'products_qty': products_qty,
        'products_set': products_set,
        'products_set_qty': products_set_qty,
        'discounts': discounts,
        'discount_limits': discount_limits,
        'discount_thresholds': discount_thresholds,
        'discount_able': discount_able,
        'discount_type': discount_type
    }
