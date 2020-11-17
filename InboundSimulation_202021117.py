import pandas as pd
import math


def simulate(data, truck_volume, site_operation, shuttle, plant_operation, speed_close):
    # 流量降序
    data.sort_values(by='日均流量', axis=0, ascending=False, inplace=True)

    result = [['Plant', 'RouteNum', 'Site', 'SiteVolume', 'RouteVolume', 'Utilization', 'TripRound', 'TripTime']]

    # 筛工厂
    plant_list = list(set(data['工厂']))
    for plant in plant_list:
        route_count = 0
        fil_plant = data[data.工厂 == plant]

        # 筛区域
        area_list = list(set(fil_plant['提货区域']))
        for area in area_list:
            fil_area = fil_plant[fil_plant.提货区域 == area]

            pickup_list = list(fil_area['提货点'])

            finish_list = []
            vmi_list = list(fil_area[fil_area.是否VMI == 1]['提货点'])
            for site in pickup_list:
                if site not in finish_list:
                    site_volume = float(fil_area[fil_area.提货点 == site]['日均流量'])
                    shift = int(fil_area[fil_area.提货点 == site]['班次'])
                    vmi = int(fil_area[fil_area.提货点 == site]['是否VMI'])
                    distance = int(fil_area[fil_area.提货点 == site]['距离'])

                    if vmi or (site_volume / shift) / 2 >= truck_volume:
                        route_count += 1
                        route_num = route_count
                        route_volume = site_volume
                        trip_round = math.ceil(site_volume / shift / truck_volume)
                        utilization = site_volume / shift / (truck_volume / 0.7 * trip_round)  # 需还原到卡车理论容积再进行运算
                        trip_time = (distance / speed_close) * 2 + site_operation + plant_operation

                        result.append(
                            [plant, route_num, site, site_volume, route_volume, utilization, trip_round, trip_time])

                        finish_list.append(site)

                    else:
                        exclude = set(finish_list + vmi_list)
                        search_range = [item for item in pickup_list if item not in exclude][1:]
                        if site_volume / shift >= truck_volume:
                            if search_range:
                                for i in search_range:
                                    i_volume = float(fil_area[fil_area.提货点 == i]['日均流量'])
                                    route_volume = site_volume + i_volume
                                    if 0.9 * truck_volume <= (route_volume / shift / 2) <= truck_volume:
                                        route_count += 1
                                        route_num = route_count
                                        trip_round = math.ceil(route_volume / shift / truck_volume)
                                        utilization = route_volume / shift / (
                                                truck_volume / 0.7 * trip_round)  # 需还原到卡车理论容积再进行运算
                                        trip_time = (
                                                            distance / speed_close) * 2 + site_operation * 2 + shuttle + plant_operation

                                        result.append(
                                            [plant, route_num, site, site_volume, route_volume, utilization, trip_round,
                                             trip_time])
                                        result.append(
                                            [plant, route_num, i, i_volume, route_volume, utilization, trip_round,
                                             trip_time])

                                        finish_list.append(site)
                                        finish_list.append(i)
                                        break

                        if site_volume / shift < truck_volume:
                            pass

    result_df = pd.DataFrame(result)
    print(result_df)


def process(site_volume, truck_volume, shift):
    if site_volume >= truck_volume * shift:
        pass


def main():
    data = pd.read_excel('Template.xlsx')
    truck_volume = 9.6 * 2.3 * 2.4 * 0.7
    site_operation = 0.25 + 0.25
    shuttle = 0.25
    plant_operation = 0.25 + 0.5
    speed_close = 25
    speed_far = 40
    simulate(data, truck_volume, site_operation, shuttle, plant_operation, speed_close)


if __name__ == '__main__':
    main()
