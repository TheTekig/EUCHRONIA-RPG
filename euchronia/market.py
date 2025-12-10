
def region_prices(item, all_item_data, world_effect=1.0, region_effect=1.0):
  price = all_item_data['item'].get('gold')  
  price = price * (world_effect * region_effect)
  return price

def market(shopkeeper, npc, all_item_data, world_effect=1.0, region_effect=1.0):
  merchant = shopkeeper[npc]
  itens_to_sell = merchant.get('stock', {})
  for i, item in intens_to_sell:
    price = region_prices(item, all_item_data, world_effect, region_effect)
    print(f"{i} - {item} [${price}]")
    

