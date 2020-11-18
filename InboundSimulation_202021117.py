import pandas as pd
import math


def simulate(data, truck_volume, deviation, site_operation, shuttle, plant_operation, speed_close, speed_far):
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
                    vmi = int(fil_region[fil_region.提货点 == site]['是否VMI'])
                    distance = int(fil_region[fil_region.提货点 == site]['距离'])

                    # VMI或提货点单班流量大于2车
                    if vmi or (site_volume / shift) / 2 >= truck_volume:
                        route_count += 1
                        route_num = route_count
                        route_volume = site_volume
                        trip_round = math.ceil(site_volume / shift / truck_volume)
                        utilization = site_volume / shift / (truck_volume / 0.7 * trip_round)  # 还原到卡车理论容积再运算
                        if distance <= 50:
                            trip_time = (distance / speed_close) * 2 + site_operation + plant_operation
                        else:
                            trip_time = (distance / speed_far) * 2 + site_operation + plant_operation

                        result.append([plant, region, route_num, site, site_volume, route_volume, utilization, trip_round, trip_time])
                        finish_list.append(site)

                    else:
                        exclude = set(finish_list + vmi_list)
                        search_range = [item for item in pickup_list if item not in exclude][1:]

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
                                            utilization = route_volume / shift / (truck_volume / 0.7 * trip_round)  # 还原到卡车理论容积再运算

                                            result.append([plant, region, route_num, site, site_volume, route_volume, utilization, trip_round, trip_time])
                                            result.append([plant, region, route_num, i, i_volume, route_volume, utilization, trip_round, trip_time])

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
                                                utilization = route_volume / shift / (truck_volume / 0.7 * trip_round)  # 还原到卡车理论容积再运算

                                                result.append([plant, region, route_num, site, site_volume, route_volume, utilization, trip_round, trip_time])
                                                result.append([plant, region, route_num, i, i_volume, route_volume, utilization, trip_round, trip_time])

                                                finish_list.append(site)
                                                finish_list.append(i)
                                                break

                        # 提货点流量小于1车，模拟三拼
                        if site_volume / shift < truck_volume:
                            if search_range:
                                for i in search_range:
                                    if search_range[1:]:
                                        for j in search_range[1:]:
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
                                                    utilization = route_volume / shift / (truck_volume / 0.7 * trip_round)  # 还原到卡车理论容积再运算

                                                    result.append([plant, region, route_num, site, site_volume, route_volume, utilization, trip_round, trip_time])
                                                    result.append([plant, region, route_num, i, i_volume, route_volume, utilization, trip_round, trip_time])
                                                    result.append([plant, region, route_num, j, j_volume, route_volume, utilization, trip_round, trip_time])

                                                    finish_list.append(site)
                                                    finish_list.append(i)
                                                    finish_list.append(j)
                                                    break
                                    break

    result_df = pd.DataFrame(result)
    result_df.columns = ['Plant', 'Region', 'RouteNum', 'Site', 'SiteVolume', 'RouteVolume', 'Utilization', 'TripRound', 'TripTime']
    result_df.to_csv('Simulation.csv', index=False, encoding='GB2312')


def main():
    data = pd.read_excel('Template.xlsx')
    truck_volume = 9.6 * 2.35 * 2.4 * 0.7
    deviation = 0.05
    site_operation = 0.25 + 0.25
    shuttle = 0.25
    plant_operation = 0.25 + 0.5
    speed_close = 25
    speed_far = 40
    simulate(data, truck_volume, deviation, site_operation, shuttle, plant_operation, speed_close, speed_far)


if __name__ == '__main__':
    main()
