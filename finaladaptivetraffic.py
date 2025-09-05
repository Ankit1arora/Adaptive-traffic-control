import pygame
import time

pygame.init()

WIDTH, HEIGHT = 1100, 800
BLACK, WHITE, RED, GREEN = (0,0,0), (255,255,255), (200,0,0), (0,200,0)
GRAY, YELLOW, CYAN = (50,50,50), (220,220,0), (0,180,180)
CAR_SIZE, CAR_SPACING = (20, 20), 6
FIXED_GREEN_TIME = 20

SCENARIO = {
    1: {"WEST": 10, "EAST": 5},
    2: {"WEST": 12, "EAST": 20}
}

WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Truly Spontaneous Adaptive Logic")
font = pygame.font.SysFont("Arial", 22, bold=True)
stats_font = pygame.font.SysFont("Consolas", 20)
car_count_font = pygame.font.SysFont("Arial", 18, bold=True)
clock = pygame.time.Clock()

directions = ["WEST", "EAST"]
waiting_fixed, waiting_adaptive = {}, {}
stats_fixed = {'total_wait_time': 0.0, 'cars_cleared': 0}
stats_adaptive = {'total_wait_time': 0.0, 'cars_cleared': 0}

simulation_started, simulation_over = False, False
fixed_current_round, adaptive_current_round = 0, 0
fixed_direction_index, adaptive_direction_index = 0, 0
start_time_fixed, start_time_adaptive = 0, 0
adaptive_green_time = 0

def fuzzy_green_time(cars):
    if cars <= 8: return 10
    elif cars <= 18: return 20
    else: return 30

def setup_initial_state():
    global fixed_current_round, adaptive_current_round
    fixed_current_round, adaptive_current_round = 1, 1
    setup_round_for_system("fixed", 1)
    setup_round_for_system("adaptive", 1)

def setup_round_for_system(system_type, round_num):
    global waiting_fixed, waiting_adaptive, fixed_direction_index, adaptive_direction_index
    global start_time_fixed, start_time_adaptive, adaptive_green_time

    if system_type == "fixed":
        waiting_fixed = SCENARIO[round_num].copy()
        fixed_direction_index = 0
        start_time_fixed = time.time()
    elif system_type == "adaptive":
        waiting_adaptive = SCENARIO[round_num].copy()
        adaptive_direction_index = 0
        start_time_adaptive = time.time()
        adaptive_green_time = fuzzy_green_time(waiting_adaptive[directions[adaptive_direction_index]])

def draw_road(x_offset, waiting, green_light, label, green_time, start_time, round_num):
    title = font.render(label, True, WHITE)
    WIN.blit(title, (x_offset + 150, 30))
    round_text_val = round_num if round_num <= len(SCENARIO) else "Finished"
    round_text = font.render(f"Round: {round_text_val}", True, YELLOW)
    WIN.blit(round_text, (x_offset + 210, 60))

    road_y, road_h = 250, 50
    pygame.draw.rect(WIN, GRAY, (x_offset, road_y, WIDTH / 2, road_h))
    pygame.draw.line(WIN, YELLOW, (x_offset, road_y + road_h//2), (x_offset + WIDTH/2, road_y + road_h//2), 2)
    lights_pos = {"WEST": (x_offset + 170, road_y+road_h), "EAST": (x_offset + 380, road_y+road_h)}
    for d, pos in lights_pos.items():
        pygame.draw.circle(WIN, GREEN if d == green_light else RED, pos, 15)

    car_pos_logic = {
        "WEST": lambda i: (x_offset+170-(i+1)*(CAR_SIZE[0]+CAR_SPACING), road_y+5),
        "EAST": lambda i: (x_offset+380+(i+1)*(CAR_SIZE[0]+CAR_SPACING), road_y+road_h-CAR_SIZE[1]-5)
    }
    for d, count in waiting.items():
        for i in range(count):
            pygame.draw.rect(WIN, CYAN, pygame.Rect(car_pos_logic[d](i), CAR_SIZE))
        if count > 0:
            first_car_pos = car_pos_logic[d](0)
            text_surface = car_count_font.render(str(count), True, WHITE)
            text_rect = text_surface.get_rect(center=(first_car_pos[0] + CAR_SIZE[0]//2, first_car_pos[1] - 15))
            WIN.blit(text_surface, text_rect)

    elapsed = time.time() - start_time if start_time > 0 else 0
    time_left = max(0, int(green_time - elapsed)) if simulation_started and round_num <= len(SCENARIO) else 0
    timer_text = font.render(f"Green: {green_light} ({time_left}s left)", True, WHITE)
    WIN.blit(timer_text, (x_offset + 150, 450))

def draw_stats(stats_f, stats_a):
    panel_y = 550
    pygame.draw.rect(WIN, BLACK, (0, panel_y, WIDTH, HEIGHT - panel_y))
    pygame.draw.line(WIN, WHITE, (0, panel_y), (WIDTH, panel_y), 3)
    fixed_title = font.render("Fixed Stats", True, WHITE); WIN.blit(fixed_title, (170, panel_y + 10))
    adaptive_title = font.render("Adaptive Stats", True, WHITE); WIN.blit(adaptive_title, (WIDTH // 2 + 150, panel_y + 10))
    avg_wait_f = stats_f['total_wait_time'] / stats_f['cars_cleared'] if stats_f['cars_cleared'] > 0 else 0
    avg_wait_a = stats_a['total_wait_time'] / stats_a['cars_cleared'] if stats_a['cars_cleared'] > 0 else 0
    def render(text, val, x, y): WIN.blit(stats_font.render(f"{text:18} {val}", True, WHITE), (x,y))
    base_y = panel_y + 50
    render("Cars Cleared:", stats_f['cars_cleared'], 50, base_y); render("Total Wait (s):", f"{stats_f['total_wait_time']:.0f}", 50, base_y + 30)
    render("Avg Wait (s):", f"{avg_wait_f:.2f}", 50, base_y + 60)
    render("Cars Cleared:", stats_a['cars_cleared'], WIDTH//2 + 50, base_y); render("Total Wait (s):", f"{stats_a['total_wait_time']:.0f}", WIDTH//2 + 50, base_y + 30)
    render("Avg Wait (s):", f"{avg_wait_a:.2f}", WIDTH//2 + 50, base_y + 60)

def draw_message(text, size, y_offset):
    msg_font = pygame.font.SysFont("Arial", size, bold=True)
    msg_text = msg_font.render(text, True, YELLOW)
    msg_rect = msg_text.get_rect(center=(WIDTH/2, HEIGHT/2 + y_offset))
    WIN.blit(msg_text, msg_rect)

last_car_leave_time_fixed, last_car_leave_time_adaptive = 0, 0
run = True
while run:
    delta_time = clock.tick(30) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT: run = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and not simulation_started:
            simulation_started = True
            setup_initial_state()

    if simulation_started and not simulation_over:
        stats_fixed['total_wait_time'] += sum(waiting_fixed.values()) * delta_time
        stats_adaptive['total_wait_time'] += sum(waiting_adaptive.values()) * delta_time

        if fixed_current_round <= len(SCENARIO):
            fixed_current_dir = directions[fixed_direction_index]
            if time.time() - last_car_leave_time_fixed > 0.4 and waiting_fixed.get(fixed_current_dir, 0) > 0:
                waiting_fixed[fixed_current_dir] -= 1; stats_fixed['cars_cleared'] += 1
                last_car_leave_time_fixed = time.time()
            if time.time() - start_time_fixed >= FIXED_GREEN_TIME:
                fixed_direction_index += 1
                if fixed_direction_index >= len(directions):
                    fixed_current_round += 1
                    if fixed_current_round <= len(SCENARIO):
                        setup_round_for_system("fixed", fixed_current_round)
                else:
                    start_time_fixed = time.time()

        if adaptive_current_round <= len(SCENARIO):
            adaptive_current_dir = directions[adaptive_direction_index]
            if time.time() - last_car_leave_time_adaptive > 0.4 and waiting_adaptive.get(adaptive_current_dir, 0) > 0:
                waiting_adaptive[adaptive_current_dir] -= 1; stats_adaptive['cars_cleared'] += 1
                last_car_leave_time_adaptive = time.time()
            
            is_timer_up = time.time() - start_time_adaptive >= adaptive_green_time
            is_lane_empty = waiting_adaptive.get(adaptive_current_dir, 0) == 0

            if is_timer_up or is_lane_empty:
                adaptive_direction_index += 1
                if adaptive_direction_index >= len(directions):
                    adaptive_current_round += 1
                    if adaptive_current_round <= len(SCENARIO):
                        setup_round_for_system("adaptive", adaptive_current_round)
                else:
                    start_time_adaptive = time.time()
                    adaptive_green_time = fuzzy_green_time(waiting_adaptive[directions[adaptive_direction_index]])

        if fixed_current_round > len(SCENARIO) and adaptive_current_round > len(SCENARIO):
            simulation_over = True

    WIN.fill(BLACK)
    if not simulation_started:
        draw_message("Press SPACEBAR to Start the Race", 40, -50)
    else:
        fixed_dir = directions[fixed_direction_index] if fixed_current_round <= len(SCENARIO) else "None"
        adaptive_dir = directions[adaptive_direction_index] if adaptive_current_round <= len(SCENARIO) else "None"
        
        draw_road(0, waiting_fixed, fixed_dir, "FIXED TIMER", FIXED_GREEN_TIME, start_time_fixed, fixed_current_round)
        draw_road(WIDTH//2, waiting_adaptive, adaptive_dir, "ADAPTIVE (FUZZY LOGIC)", adaptive_green_time, start_time_adaptive, adaptive_current_round)
        draw_stats(stats_fixed, stats_adaptive)
        if simulation_over:
            draw_message("Simulation Complete!", 50, -20)
            
    pygame.display.update()

pygame.quit()