#!/usr/bin/env python3
from time import sleep
from pycloak.dbug import Benchmark

def code_to_time(t):
   sleep(t)

def benchmark_result(interval):
   print("code_to_time took %s" % interval)

with Benchmark():
   code_to_time(5)

with Benchmark(benchmark_result):
   code_to_time(2)


