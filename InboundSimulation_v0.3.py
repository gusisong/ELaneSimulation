"""
Author: Gu Sisong
Version: 20201215
Updates:
排程目标调整为单班至少1车
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
            for site in pickup_list:
                if site not in finish_list:
                    site_volume = float(fil_region[fil_region.提货点 == site]['日均流量'])
                    shift = int(fil_region[fil_region.提货点 == site]['班次'])
                    distance = int(fil_region[fil_region.提货点 == site]['距离'])
                    vmi = int(fil_region[fil_region.提货点 == site]['是否VMI'])
                    avg_speed = speed_close if distance <= 50 else speed_far

                    # 提货点单班流量>1车
                    if vmi or site_volume / shift >= truck_volume:
                        route_volume = site_volume
                        route_sites = 1
                        trip_time = site_operation * route_sites + shuttle * (route_sites - 1) + plant_operation + (distance / avg_speed) * 2
                        vmi_tag = 'Y' if vmi else 'N'
                        route_count += 1
                        route_num = route_count
                        trip_round = round(route_volume / ((truck_volume / loading_rate) * 0.75)) if (route_volume / truck_volume) >= 2 else 2
                        utilization = route_volume / (truck_volume / loading_rate * trip_round)  # 还原到卡车理论容积再运算

                        # 控制装载率上限
                        while utilization >= 0.75:
                            trip_round += 1
                            utilization = route_volume / (truck_volume / loading_rate * trip_round)  # 还原到卡车理论容积再运算

                        truck_demand = math.ceil(trip_round * trip_time / 20)
                        route_type = 'DR'

                        result.append([plant, region, route_num, route_type, site, vmi_tag, site_volume, route_volume, utilization, trip_round, trip_time, truck_demand])
                        finish_list.append(site)

                    # 提货点单班流量<1车
                    else:
                        # 排除VMI和已规划过的提货点
                        exclude = set(finish_list + vmi_list)
                        search_range = [item for item in pickup_list if item not in exclude][1:]

                        if search_range:
                            success = False
                            # 尝试MR2线路
                            for i in search_range:
                                i_volume = float(fil_region[fil_region.提货点 == i]['日均流量'])
                                route_volume = site_volume + i_volume

                                # 装载率是否符合
                                if abs((route_volume / shift) - truck_volume) <= deviation * (truck_volume / loading_rate):
                                    route_sites = 2
                                    trip_time = site_operation * route_sites + shuttle * (route_sites - 1) + plant_operation + (distance / avg_speed) * 2

                                    # 周转时间是否符合
                                    if trip_time <= 10:
                                        vmi_tag = 'Y' if vmi else 'N'
                                        route_count += 1
                                        route_num = route_count
                                        trip_round = round(route_volume / truck_volume)
                                        utilization = route_volume / (truck_volume / loading_rate * trip_round)  # 还原到卡车理论容积再运算
                                        truck_demand = math.ceil(trip_round * trip_time / 20)
                                        route_type = 'MR'

                                        result.append([plant, region, route_num, route_type, site, vmi_tag, site_volume, route_volume, utilization, trip_round, trip_time, truck_demand])
                                        result.append([plant, region, route_num, route_type, i, vmi_tag, i_volume, route_volume, utilization, trip_round, trip_time, truck_demand])

                                        finish_list.append(site)
                                        finish_list.append(i)

                                        success = True
                                        break

                            if not success:
                                # 尝试MR3线路
                                if search_range[1:]:
                                    for n, i in enumerate(search_range):
                                        if search_range[(n + 1):]:
                                            for j in search_range[(n + 1):]:
                                                i_volume = float(fil_region[fil_region.提货点 == i]['日均流量'])
                                                j_volume = float(fil_region[fil_region.提货点 == j]['日均流量'])
                                                route_volume = site_volume + i_volume + j_volume

                                                if route_volume / shift < (loading_rate - deviation) * (truck_volume / loading_rate):
                                                    break

                                                # 装载率是否符合
                                                if abs((route_volume / shift) - truck_volume) <= deviation * (truck_volume / loading_rate):
                                                    route_sites = 3
                                                    trip_time = site_operation * route_sites + shuttle * (route_sites - 1) + plant_operation + (distance / avg_speed) * 2

                                                    if trip_time <= 10:
                                                        vmi_tag = 'Y' if vmi else 'N'
                                                        route_count += 1
                                                        route_num = route_count
                                                        trip_round = round(route_volume / truck_volume)
                                                        utilization = route_volume / (truck_volume / loading_rate * trip_round)  # 还原到卡车理论容积再运算
                                                        truck_demand = math.ceil(trip_round * trip_time / 20)
                                                        route_type = 'MR'

                                                        result.append(
                                                            [plant, region, route_num, route_type, site, vmi_tag, site_volume, route_volume, utilization, trip_round, trip_time, truck_demand])
                                                        result.append([plant, region, route_num, route_type, i, vmi_tag, i_volume, route_volume, utilization, trip_round, trip_time, truck_demand])
                                                        result.append([plant, region, route_num, route_type, j, vmi_tag, j_volume, route_volume, utilization, trip_round, trip_time, truck_demand])

                                                        # print('3提货点:' + str(site))
                                                        # print(search_range)
                                                        # print(search_range[1:])

                                                        finish_list.append(site)
                                                        finish_list.append(i)
                                                        finish_list.append(j)
                                                        success = True
                                                        break
                                            if success:
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
                        vmi_tag = 'N'
                        avg_speed = speed_close if distance <= 50 else speed_far

                        # 判断单点线路运输时间是否已经超出10小时
                        trip_time_min = site_operation + plant_operation + (distance / avg_speed) * 2
                        trip_time_max = site_operation * rest_site + shuttle * (rest_site - 1) + plant_operation + (distance / avg_speed) * 2
                        rest_route = math.ceil(trip_time_max / 10) - 1 if trip_time_min >= 10 else math.ceil(math.ceil(trip_time_max / 10))

                        trip_round = 2 * rest_route
                        utilization = rest_volume / (truck_volume * rest_route / loading_rate * trip_round)  # 还原到卡车理论容积再运算

                        # 控制装载率上限
                        while utilization >= 0.75:
                            trip_round += rest_route
                            utilization = rest_volume / (truck_volume * rest_route / loading_rate * trip_round)  # 还原到卡车理论容积再运算

                        trip_time = site_operation * (rest_site / rest_route) + shuttle * (rest_site / rest_route - 1) + plant_operation + (distance / avg_speed) * 2
                        truck_demand = math.ceil(trip_round * trip_time / 20)
                        route_type = 'MR'

                        result.append([plant, region, route_num, route_type, site, vmi_tag, site_volume, rest_volume, utilization, trip_round, trip_time, truck_demand])

                        result_df = pd.DataFrame(result)
                        result_df.columns = ['Plant', 'Region', 'RouteNum', 'RouteType', 'Site', 'VMI', 'SiteVolume', 'RouteVolume', 'Utilization', 'TripRound', 'TripTime', 'TruckDemand']
                        result_df.to_csv('Simulation.csv', index=False, encoding='GB2312')


def main():
    data = pd.read_excel('Template.xlsx')  # 读取模板数据
    loading_rate = 0.65  # 目标装载率
    truck_volume = 9.6 * 2.35 * 2.4 * loading_rate  # 9.6m标准卡车容积
    deviation = 0.05  # 装载率偏差范围±5%
    site_operation = 0.25 + 0.33  # 提货点等待&操作时间
    shuttle = 0.33  # 提货点之间短驳运输时间
    plant_operation = 0.25 + 0.5  # 工厂等待&操作时间
    speed_close = 25  # 市内卡车均速
    speed_far = 50  # 长途卡车均速
    simulate(data, truck_volume, loading_rate, deviation, site_operation, shuttle, plant_operation, speed_close, speed_far)


if __name__ == '__main__':
    main()
