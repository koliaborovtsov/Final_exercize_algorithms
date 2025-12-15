import heapq
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import sys


class CityGraph:

	def __init__(self):
		self.cities = {}
		self.name_to_id = {}
		self.graph = defaultdict(list)

	def add_city(self, city_id: int, name: str):
		name = name.strip()
		self.cities[city_id] = name
		self.name_to_id[name] = city_id

	def add_road(self, id1: int, id2: int, distance: int, time: int,
	             cost: int):
		self.graph[id1].append((id2, distance, time, cost))
		self.graph[id2].append((id1, distance, time, cost))

	def get_id_by_name(self, name: str) -> Optional[int]:
		return self.name_to_id.get(name.strip())

	def get_name_by_id(self, city_id: int) -> str:
		return self.cities.get(city_id, "")


class RouteOptimizer:

	def __init__(self, graph: CityGraph):
		self.graph = graph

	def find_optimal_path(
	        self, start_id: int, end_id: int,
	        criterion: int) -> Tuple[List[int], Tuple[int, int, int]]:
		"""
		0 - расстояние, 1 - время, 2 - стоимость
		Возвращает (путь, (расстояние, время, стоимость))
		"""
		distances = {node: float('inf') for node in self.graph.graph}
		prev = {node: None for node in self.graph.graph}
		total_params = {node: (0, 0, 0) for node in self.graph.graph}

		distances[start_id] = 0
		total_params[start_id] = (0, 0, 0)

		heap = [(0, start_id)]

		while heap:
			current_dist, current = heapq.heappop(heap)

			if current_dist > distances[current]:
				continue

			if current == end_id:
				break

			for neighbor, dist, time, cost in self.graph.graph[current]:
				params = (dist, time, cost)
				new_criterion_dist = current_dist + params[criterion]

				if new_criterion_dist < distances[neighbor]:
					distances[neighbor] = new_criterion_dist
					prev[neighbor] = current
					old_params = total_params[current]
					total_params[neighbor] = (old_params[0] + dist,
					                          old_params[1] + time,
					                          old_params[2] + cost)
					heapq.heappush(heap, (new_criterion_dist, neighbor))

		if distances[end_id] == float('inf'):
			return [], (0, 0, 0)

		path = []
		current = end_id
		while current is not None:
			path.append(current)
			current = prev[current]
		path.reverse()

		return path, total_params[end_id]

	def get_all_optimal_routes(
	        self, start: str,
	        end: str) -> Dict[str, Tuple[List[int], Tuple[int, int, int]]]:
		start_id = self.graph.get_id_by_name(start)
		end_id = self.graph.get_id_by_name(end)

		if not start_id or not end_id:
			return {}

		results = {}
		criteria = [("ДЛИНА", 0), ("ВРЕМЯ", 1), ("СТОИМОСТЬ", 2)]

		for name, idx in criteria:
			path, params = self.find_optimal_path(start_id, end_id, idx)
			if path:
				results[name] = (path, params)

		return results

	def find_compromise_route(
	        self, routes: Dict[str, Tuple[List[int], Tuple[int, int, int]]],
	        priorities: str) -> Tuple[List[int], Tuple[int, int, int]]:
		priorities_str = priorities.strip("()").replace(" ", "")
		priority_order = priorities_str.split(",")

		criterion_map = {"Д": "ДЛИНА", "В": "ВРЕМЯ", "С": "СТОИМОСТЬ"}

		for criterion in priority_order:
			route_key = criterion_map.get(criterion)
			if route_key in routes:
				return routes[route_key]

		return ([], (0, 0, 0))


def parse_input(filename: str) -> Tuple[CityGraph, List[Tuple[str, str, str]]]:
	graph = CityGraph()
	requests = []

	try:
		with open(filename, 'r', encoding='utf-8') as f:
			content = f.readlines()
	except FileNotFoundError:
		print(f"Файл {filename} не найден")
		return graph, requests

	current_section = None

	for line in content:
		line = line.strip()

		if not line:
			continue

		if line.startswith('[') and line.endswith(']'):
			current_section = line
			continue

		if current_section == "[CITIES]":
			if ':' in line:
				parts = line.split(':', 1)
				if len(parts) == 2:
					try:
						city_id = int(parts[0].strip())
						city_name = parts[1].strip()
						graph.add_city(city_id, city_name)
					except ValueError:
						print(f"Некорректный ID города в строке: {line}")

		elif current_section == "[ROADS]":
			if ':' in line:
				# Разделяем на части: города и параметры
				road_parts = line.split(':', 1)
				cities_part = road_parts[0].strip()
				params_part = road_parts[1].strip() if len(road_parts) > 1 else ""

				if '-' in cities_part:
					city_parts = cities_part.split('-')
					if len(city_parts) == 2:
						try:
							id1 = int(city_parts[0].strip())
							id2 = int(city_parts[1].strip())

							if params_part:
								params = []
								for param in params_part.split(','):
									param = param.strip()
									if param:
										params.append(int(param))

								if len(params) >= 3:
									distance = params[0]
									time = params[1]
									cost = params[2]
									graph.add_road(id1, id2, distance, time, cost)
								else:
									print(f"Недостаточно параметров в строке: {line}")
							else:
								print(f"Отсутствуют параметры в строке: {line}")

						except ValueError as e:
							print(f"Некорректные данные в строке: {line}")
							print(f"Ошибка {e}")

		elif current_section == "[REQUESTS]":
			if '->' in line:
				if '|' in line:
					route_part, priority_part = line.split('|', 1)
				else:
					route_part, priority_part = line, "(Д,В,С)"

				route_part = route_part.strip()
				priority_part = priority_part.strip()

				cities = route_part.split('->', 1)
				if len(cities) == 2:
					start = cities[0].strip()
					end = cities[1].strip()
					requests.append((start, end, priority_part))

	return graph, requests


def format_path(path: List[int], graph: CityGraph) -> str:
	return " -> ".join(graph.get_name_by_id(city_id) for city_id in path)


def write_output(filename: str, results: List[str]):
	with open(filename, 'w', encoding='utf-8') as f:
		for result in results:
			f.write(result + '\n')


def main():
	input_file = "input.txt"
	output_file = "output.txt"

	try:
		graph, requests = parse_input(input_file)
		optimizer = RouteOptimizer(graph)

		all_results = []

		for start_city, end_city, priorities in requests:
			routes = optimizer.get_all_optimal_routes(start_city, end_city)

			if not routes:
				all_results.append(f"Нет пути между {start_city} и {end_city}")
				continue

			for criterion in ["ДЛИНА", "ВРЕМЯ", "СТОИМОСТЬ"]:
				if criterion in routes:
					path, params = routes[criterion]
					path_str = format_path(path, graph)
					result_line = f"{criterion}: {path_str} | Д={params[0]}, В={params[1]}, С={params[2]}"
					all_results.append(result_line)
				else:
					all_results.append(f"{criterion}: Нет пути")

			compromise_path, compromise_params = optimizer.find_compromise_route(
			    routes, priorities)
			if compromise_path:
				path_str = format_path(compromise_path, graph)
				result_line = f"КОМПРОМИСС: {path_str} | Д={compromise_params[0]}, В={compromise_params[1]}, С={compromise_params[2]}"
				all_results.append(result_line)
			else:
				all_results.append("КОМПРОМИСС: Нет пути")

			all_results.append("")

		write_output(output_file, all_results)
		print(f"Результаты записаны в {output_file}")

	except FileNotFoundError:
		print(f"Файл {input_file} не найден")
		sys.exit(1)
	except Exception as e:
		print(f"Ошибка {e}")
		sys.exit(1)


if __name__ == "__main__":
	main()
