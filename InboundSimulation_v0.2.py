"""
Author: Gu Sisong
Version: 20201123
Updates: 修正MR3逻辑
"""

import pandas as pd
import math


def simulate(data, truck_volume, loading_rate, deviation, site_operation, shuttle, plant_operation, speed_close, speed_far):
    # 流量降序
    data.sort_values(by='日均流量', axis=0, ascending=False, inplace=True)
    result = []

    # 筛工厂
    plant_list = list(set(data['工厂']))
    for plant in plant_list:
        route_count = 0
        fil_plant = data[data.工厂 == plant]

        # 筛区域
        region_list = list(set(fil_plant['提货区域']))
        for region in region_list:
            fil_region = fil_plant[fil_plant.提货区域 == region]
            pickup_list = list(fil_region['提货点'])
            finish_list = []
            vmi_list = list(fil_region[fil_region.是否VMI == 1]['提货点'])
            for n, site in enumerate(pickup_list):
                if site not in finish_list:
                    site_volume = float(fil_region[fil_region.提货点 == site]['日均流量'])
                    shift = int(fil_region[fil_region.提货点 == site]['班次'])
                    distance = int(fil_region[fil_region.提货点 == site]['距离'])
                    vmi = int(fil_region[fil_region.提货点 == site]['是否VMI'])

                    # 提货点单班流量大于2车
                    if vmi or site_volume / shift / 2 >= truck_volume:
                        trip_round = round(site_volume / shift / truck_volume)
                        if trip_round <= 1:
                            trip_round = 2

                        route_count += 1
                        route_num = route_count
                        route_volume = site_volume
                        utilization = site_volume / shift / (truck_volume / loading_rate * trip_round)  # 还原到卡车理论容积再运算
                        if distance <= 50:
                            trip_time = (distance / speed_close) * 2 + site_operation + plant_operation
                        else:
                            trip_time = (distance / speed_far) * 2 + site_operation + plant_operation
                        truck_demand = math.ceil(trip_round * trip_time / 10)
                        vmi_tag = 'Y' if vmi else 'N'

                        result.append([plant, region, route_num, site, vmi_tag, site_volume, route_volume, utilization,
                                       trip_round, trip_time, truck_demand])
                        finish_list.append(site)

                    else:
                        # 排除VMI和已规划过的提货点
                        exclude = set(finish_list + vmi_list)
                        search_range = [item for item in pickup_list[n:] if item not in exclude][1:]

                        # 提货点单班流量大于1车，模拟双拼
                        if site_volume / shift >= truck_volume:
                            if search_range:
                                origin_route_count = route_count
                                # 模拟2轮
                                for i in search_range:
                                    i_volume = float(fil_region[fil_region.提货点 == i]['日均流量'])
                                    route_volume = site_volume + i_volume

                                    if (1 - deviation) * truck_volume <= (route_volume / shift / 2) <= (1 + deviation) * truck_volume:
                                        if distance <= 50:
                                            trip_time = site_operation * 2 + shuttle + plant_operation + (distance / speed_close) * 2
                                        else:
                                            trip_time = site_operation * 2 + shuttle + plant_operation + (distance / speed_far) * 2

                                        if trip_time <= (10 / 2):
                                            route_count += 1
                                            route_num = route_count
                                            trip_round = 2
                                            utilization = route_volume / shift / (truck_volume / loading_rate * trip_round)  # 还原到卡车理论容积再运算
                                            truck_demand = math.ceil(trip_round * trip_time / 10)
                                            vmi_tag = 'N'

                                            result.append([plant, region, route_num, site, vmi_tag, site_volume, route_volume, utilization, trip_round, trip_time, truck_demand])
                                            result.append([plant, region, route_num, i, vmi_tag, i_volume, route_volume, utilization, trip_round, trip_time, truck_demand])

                                            finish_list.append(site)
                                            finish_list.append(i)
                                            break

                                # 不满足2轮，模拟3轮
                                if route_count == origin_route_count:
                                    for i in search_range:
                                        i_volume = float(fil_region[fil_region.提货点 == i]['日均流量'])
                                        route_volume = site_volume + i_volume

                                        if (1 - deviation) * truck_volume <= (route_volume / shift / 3) <= (1 + deviation) * truck_volume:
                                            if distance <= 50:
                                                trip_time = site_operation * 3 + shuttle * 2 + plant_operation + (distance / speed_close) * 2
                                            else:
                                                trip_time = site_operation * 3 + shuttle * 2 + plant_operation + (distance / speed_far) * 2

                                            if trip_time <= (10 / 3):
                                                route_count += 1
                                                route_num = route_count
                                                trip_round = 3
                                                utilization = route_volume / shift / (truck_volume / loading_rate * trip_round)  # 还原到卡车理论容积再运算
                                                truck_demand = math.ceil(trip_round * trip_time / 10)
                                                vmi_tag = 'N'

                                                result.append([plant, region, route_num, site, vmi_tag, site_volume, route_volume, utilization, trip_round, trip_time, truck_demand])
                                                result.append([plant, region, route_num, i, vmi_tag, i_volume, route_volume, utilization, trip_round, trip_time, truck_demand])

                                                finish_list.append(site)
                                                finish_list.append(i)
                                                break

                        # 提货点流量小于1车，模拟三拼
                        if site_volume / shift < truck_volume:
                            success = False
                            if search_range:
                                for n, i in enumerate(search_range):
                                    if search_range[(n + 1):]:
                                        if success:
                                            break
                                        for j in search_range[(n + 1):]:
                                            i_volume = float(fil_region[fil_region.提货点 == i]['日均流量'])
                                            j_volume = float(fil_region[fil_region.提货点 == j]['日均流量'])
                                            route_volume = site_volume + i_volume + j_volume

                                            if (1 - deviation) * truck_volume <= (route_volume / shift / 2) <= (1 + deviation) * truck_volume:
                                                if distance <= 50:
                                                    trip_time = site_operation * 3 + shuttle * 2 + plant_operation + (distance / speed_close) * 2
                                                else:
                                                    trip_time = site_operation * 3 + shuttle * 2 + plant_operation + (distance / speed_far) * 2

                                                if trip_time <= (10 / 2):
                                                    route_count += 1
                                                    route_num = route_count
                                                    trip_round = 2
                                                    utilization = route_volume / shift / (truck_volume / loading_rate * trip_round)  # 还原到卡车理论容积再运算
                                                    truck_demand = math.ceil(trip_round * trip_time / 10)
                                                    vmi_tag = 'N'

                                                    result.append([plant, region, route_num, site, vmi_tag, site_volume, route_volume, utilization, trip_round, trip_time, truck_demand])
                                                    result.append([plant, region, route_num, i, vmi_tag, i_volume, route_volume, utilization, trip_round, trip_time, truck_demand])
                                                    result.append([plant, region, route_num, j, vmi_tag, j_volume, route_volume, utilization, trip_round, trip_time, truck_demand])

                                                    print('3提货点:' + str(site))
                                                    print(search_range)
                                                    print(search_range[1:])

                                                    finish_list.append(site)
                                                    finish_list.append(i)
                                                    finish_list.append(j)

                                                    success = True
                                                    break

            # 在剩余站点中规划需要多部卡车运作的线路
            for n, site in enumerate(pickup_list):
                if site not in finish_list:
                    site_volume = float(fil_region[fil_region.提货点 == site]['日均流量'])
                    shift = int(fil_region[fil_region.提货点 == site]['班次'])
                    distance = int(fil_region[fil_region.提货点 == site]['距离'])

                    # 排除VMI和已规划过的提货点
                    exclude = set(finish_list + vmi_list)
                    search_range = [item for item in pickup_list[n:] if item not in exclude][1:]

                    # 提货点单班流量大于1车，模拟双拼
                    if site_volume / shift >= truck_volume:
                        if search_range:
                            origin_route_count = route_count
                            # 模拟2轮
                            for i in search_range:
                                i_volume = float(fil_region[fil_region.提货点 == i]['日均流量'])
                                route_volume = site_volume + i_volume

                                if (1 - deviation) * truck_volume <= (route_volume / shift / 2) <= (1 + deviation) * truck_volume:
                                    if distance <= 50:
                                        trip_time = site_operation * 2 + shuttle + plant_operation + (distance / speed_close) * 2
                                    else:
                                        trip_time = site_operation * 2 + shuttle + plant_operation + (distance / speed_far) * 2

                                    route_count += 1
                                    route_num = route_count
                                    trip_round = 2
                                    utilization = route_volume / shift / (truck_volume / loading_rate * trip_round)  # 还原到卡车理论容积再运算

                                    truck_demand = math.ceil(trip_round * trip_time / 10)

                                    vmi_tag = 'N'

                                    result.append([plant, region, route_num, site, vmi_tag, site_volume, route_volume, utilization, trip_round, trip_time, truck_demand])
                                    result.append([plant, region, route_num, i, vmi_tag, i_volume, route_volume, utilization, trip_round, trip_time, truck_demand])

                                    finish_list.append(site)
                                    finish_list.append(i)
                                    break

                            # 不满足2轮，模拟3轮
                            if route_count == origin_route_count:
                                for i in search_range:
                                    i_volume = float(fil_region[fil_region.提货点 == i]['日均流量'])
                                    route_volume = site_volume + i_volume

                                    if (1 - deviation) * truck_volume <= (route_volume / shift / 3) <= (1 + deviation) * truck_volume:
                                        if distance <= 50:
                                            trip_time = site_operation * 3 + shuttle * 2 + plant_operation + (distance / speed_close) * 2
                                        else:
                                            trip_time = site_operation * 3 + shuttle * 2 + plant_operation + (distance / speed_far) * 2

                                        route_count += 1
                                        route_num = route_count
                                        trip_round = 3
                                        utilization = route_volume / shift / (truck_volume / loading_rate * trip_round)  # 还原到卡车理论容积再运算

                                        truck_demand = math.ceil(trip_round * trip_time / 10)

                                        vmi_tag = 'N'

                                        result.append([plant, region, route_num, site, vmi_tag, site_volume, route_volume, utilization, trip_round, trip_time, truck_demand])
                                        result.append([plant, region, route_num, i, vmi_tag, i_volume, route_volume, utilization, trip_round, trip_time, truck_demand])

                                        finish_list.append(site)
                                        finish_list.append(i)
                                        break

                    # 提货点流量小于1车，模拟三拼
                    if site_volume / shift < truck_volume:
                        success = False
                        if search_range:
                            for n, i in enumerate(search_range):
                                if search_range[(n + 1):]:
                                    if success:
                                        break
                                    for j in search_range[(n + 1):]:
                                        i_volume = float(fil_region[fil_region.提货点 == i]['日均流量'])
                                        j_volume = float(fil_region[fil_region.提货点 == j]['日均流量'])
                                        route_volume = site_volume + i_volume + j_volume

                                        if (1 - deviation) * truck_volume <= (route_volume / shift / 2) <= (1 + deviation) * truck_volume:
                                            if distance <= 50:
                                                trip_time = site_operation * 3 + shuttle * 2 + plant_operation + (distance / speed_close) * 2
                                            else:
                                                trip_time = site_operation * 3 + shuttle * 2 + plant_operation + (distance / speed_far) * 2

                                            route_count += 1
                                            route_num = route_count
                                            trip_round = 2
                                            utilization = route_volume / shift / (truck_volume / loading_rate * trip_round)  # 还原到卡车理论容积再运算

                                            truck_demand = math.ceil(trip_round * trip_time / 10)

                                            vmi_tag = 'N'

                                            result.append([plant, region, route_num, site, vmi_tag, site_volume, route_volume, utilization, trip_round, trip_time, truck_demand])
                                            result.append([plant, region, route_num, i, vmi_tag, i_volume, route_volume, utilization, trip_round, trip_time, truck_demand])
                                            result.append([plant, region, route_num, j, vmi_tag, j_volume, route_volume, utilization, trip_round, trip_time, truck_demand])

                                            print('3提货点:' + str(site))
                                            print(search_range)
                                            print(search_range[1:])

                                            finish_list.append(site)
                                            finish_list.append(i)
                                            finish_list.append(j)

                                            success = True
                                            break

            # 其余站点合并规划
            if len(finish_list) < len(pickup_list):
                route_count += 1
                route_num = route_count

                rest_volume = 0
                rest_site = 0
                for site in pickup_list:
                    if site not in finish_list:
                        site_volume = float(fil_region[fil_region.提货点 == site]['日均流量'])
                        rest_volume += site_volume
                        rest_site += 1

                for site in pickup_list:
                    if site not in finish_list:
                        site_volume = float(fil_region[fil_region.提货点 == site]['日均流量'])
                        shift = int(fil_region[fil_region.提货点 == site]['班次'])
                        distance = int(fil_region[fil_region.提货点 == site]['距离'])
                        trip_round = 2
                        utilization = rest_volume / shift / (truck_volume * math.ceil(rest_site / 5) / loading_rate * trip_round)  # 还原到卡车理论容积再运算

                        if distance <= 50:
                            trip_time = site_operation * (rest_site / math.ceil(rest_site / 5)) + shuttle * (rest_site / math.ceil(rest_site / 5) - 1) + plant_operation + (distance / speed_close) * 2
                        else:
                            trip_time = site_operation * (rest_site / math.ceil(rest_site / 5)) + shuttle * (rest_site / math.ceil(rest_site / 5) - 1) + plant_operation + (distance / speed_far) * 2

                        truck_demand = math.ceil(trip_round * trip_time / 10) * math.ceil(rest_site / 5)

                        vmi_tag = 'N'

                        result.append([plant, region, route_num, site, vmi_tag, site_volume, rest_volume, utilization, trip_round, trip_time, truck_demand])

    result_df = pd.DataFrame(result)
    result_df.columns = ['Plant', 'Region', 'RouteNum', 'Site', 'VMI', 'SiteVolume', 'RouteVolume', 'Utilization', 'TripRound', 'TripTime', 'TruckDemand']
    result_df.to_csv('Simulation.csv', index=False, encoding='GB2312')


def main():
    data = pd.read_excel('Template.xlsx')
    loading_rate = 0.65
    truck_volume = 9.6 * 2.35 * 2.4 * loading_rate
    deviation = 0.05
    site_operation = 0.25 + 0.25
    shuttle = 0.25
    plant_operation = 0.25 + 0.5
    speed_close = 25
    speed_far = 50
    simulate(data, truck_volume, loading_rate, deviation, site_operation, shuttle, plant_operation, speed_close, speed_far)


if __name__ == '__main__':
    main()
