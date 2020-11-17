import pandas as pd
import math


def simulate(data, truck_volume, site_operation, plant_operation, speed_close):
    # 流量降序
    data.sort_values(by='日均流量', axis=0, ascending=False, inplace=True)

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

            passed_list = []
            for site in pickup_list:
                if site not in passed_list:
                    site_volume = float(fil_area[fil_area.提货点 == site]['日均流量'])
                    shift = int(fil_area[fil_area.提货点 == site]['班次'])
                    VMI = int(fil_area[fil_area.提货点 == site]['是否VMI'])
                    distance = int(fil_area[fil_area.提货点 == site]['距离'])

                    if VMI:
                        route_count += 1
                        route_num = route_count
                        trip_round = math.ceil(site_volume / shift / truck_volume)
                        utilization = site_volume / shift / (truck_volume / 0.7 * trip_round)  # 需还原到卡车理论容积再进行运算
                        trip_time = (distance / speed_close) * 2 + 0.5 + plant_operation  # 点对点线路的站点操作时间默认0.5h

                        passed_list.append(site)

                        print(route_num, trip_round, site_volume, utilization, trip_time)


                    else:
                        pass


def process(site_volume, truck_volume, shift):
    if site_volume >= truck_volume * shift:
        pass


def main():
    data = pd.read_excel('Template.xlsx')
    truck_volume = 9.6 * 2.35 * 2.4 * 0.7
    site_operation = 0.25 + 0.25
    plant_operation = 0.25 + 0.5
    speed_close = 25
    speed_far = 40
    simulate(data, truck_volume, site_operation, plant_operation, speed_close)


if __name__ == '__main__':
    main()
