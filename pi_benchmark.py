import multiprocessing
import time
import math
import sys

def calculate_pi_chunk(process_id, total_processes, duration, shared_iters, shared_sum):
    """
    각 코어에서 실행될 파이 계산 작업
    """
    start_time = time.time()
    end_time = start_time + duration
    
    n = process_id
    iters = 0
    local_s = 0.0
    
    while True:
        now = time.time()
        if now >= end_time:
            break
            
        # 남은 시간에 따라 배치 크기를 동적으로 조절합니다.
        # 기존에는 500만 번씩 딱 떨어지게 연산해서 숫자가 인위적으로 보였지만,
        # 이제는 8192(2의 13승) 단위로 쪼개고, 마지막 0.05초는 17 단위로 쪼개어
        # 1. 숫자가 기계적이지 않고 유기적으로 올라가게 하고
        # 2. 60초 종료 시점에 오차 없이 아주 정확하게 연산을 끝내도록 합니다.
        time_left = end_time - now
        if time_left > 0.05:
            current_batch = 8192
        else:
            current_batch = 17
            
        for _ in range(current_batch):
            denom = 2 * n + 1
            if n % 2 == 0:
                local_s += 1.0 / denom
            else:
                local_s -= 1.0 / denom
            n += total_processes
            
        iters += current_batch
        
        # 락(lock)이 없는 독립적인 배열 인덱스를 사용하여 딜레이 없이 실시간 기록
        shared_iters[process_id] = iters
        shared_sum[process_id] = local_s

if __name__ == '__main__':
    # Windows 환경에서 multiprocessing을 안전하게 사용하기 위한 설정
    multiprocessing.freeze_support()
    
    duration = 60  # 1분 (60초)
    cores = multiprocessing.cpu_count()
    
    print("=" * 65)
    print("         CPU 멀티코어 원주율(Pi) 벤치마크 (실시간 모니터링)  ")
    print("=" * 65)
    print(f"감지된 CPU 코어 수: {cores} 코어")
    print(f"벤치마크 진행 시간: {duration} 초")
    print("-" * 65)
    print("연산을 시작합니다... (종료 시까지 창을 닫지 마세요)")
    print("-" * 65)
    
    # 락(lock) 오버헤드를 완전히 없애기 위해 프로세스별 독립적인 공간(Array) 사용
    shared_iters = multiprocessing.Array('q', cores, lock=False)
    shared_sum = multiprocessing.Array('d', cores, lock=False)
    
    processes = []
    # 각 프로세스에 작업 할당 및 시작
    for i in range(cores):
        p = multiprocessing.Process(target=calculate_pi_chunk, args=(i, cores, duration, shared_iters, shared_sum))
        p.start()
        processes.append(p)
    
    start_wall_time = time.time()
    
    # 메인 프로세스: 0.1초마다 공유 변수 값을 읽어서 화면에 매우 부드럽게 실시간 출력
    while True:
        elapsed = time.time() - start_wall_time
        if elapsed >= duration:
            break
            
        # 각 코어의 현재까지의 연산 횟수와 파이 값을 취합
        current_iters = sum(shared_iters)
        current_sum = sum(shared_sum)
            
        current_pi = current_sum * 4
        
        # \r을 사용하여 같은 줄을 덮어쓰며, 0.1초 단위의 빠른 새로고침으로 "진짜 돌아가는 느낌"을 줍니다.
        sys.stdout.write(f"\r[실시간] 경과: {elapsed:5.2f}초 | 연산: {current_iters:13,} 회 | 파이값: {current_pi:.11f}   ")
        sys.stdout.flush()
        
        time.sleep(0.1)
        
    # 모든 프로세스가 종료될 때까지 대기
    for p in processes:
        p.join()
        
    actual_duration = time.time() - start_wall_time
    
    final_iters = sum(shared_iters)
    final_pi = sum(shared_sum) * 4
    
    print("\n\n" + "=" * 65)
    print("                  벤치마크 테스트 완료!  ")
    print("=" * 65)
    print(f"총 연산 횟수(점수): {final_iters:,} 회")
    print(f"초당 연산력(OPS):   {int(final_iters / actual_duration):,} 회/초")
    print("-" * 65)
    print(f"최종 계산된 파이:   {final_pi:.15f}")
    print(f"실제 파이(math.pi): {math.pi:.15f}")
    print(f"오차 범위:          {abs(math.pi - final_pi):.15e}")
    print("=" * 65)
    
    # 탐색기에서 더블 클릭으로 실행 시, 결과창이 바로 닫히는(튕기는) 현상 방지
    input("\n테스트가 종료되었습니다. 엔터(Enter) 키를 누르면 프로그램이 종료됩니다...")
