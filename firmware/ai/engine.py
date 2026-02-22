"""
RoboOS AI Engine — محرك الذكاء الاصطناعي
=========================================
نظام AI متكامل يشمل:
  - PID Controller ذكي مع Auto-Tune
  - Fuzzy Logic للتحكم التكيفي
  - Reinforcement Learning بسيط (Q-Table)
  - Anomaly Detection لمراقبة المستشعرات
  - Path Planning (A* Algorithm)
  - Neural Network خفيف للتصنيف
  - Gesture Recognition من بيانات IMU
"""

import math
import time
import json
import random
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque
from enum import Enum


# ─────────────────────────────────────────────────────────────
# 1. PID CONTROLLER WITH AUTO-TUNE
# ─────────────────────────────────────────────────────────────

class PIDController:
    """
    PID Controller ذكي مع Auto-Tuning تلقائي
    يستخدم لتحقيق الاستقرار في حركة الروبوت
    """

    def __init__(self, kp: float = 1.0, ki: float = 0.0, kd: float = 0.0,
                 output_min: float = -255, output_max: float = 255,
                 name: str = "PID"):
        self.name = name
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_min = output_min
        self.output_max = output_max

        self._prev_error = 0.0
        self._integral = 0.0
        self._prev_time = time.time()
        self._error_history: deque = deque(maxlen=100)

        # Auto-tune state
        self._autotune_active = False
        self._autotune_setpoint = 0.0
        self._autotune_output = 0.0
        self._oscillations: List[float] = []
        self._last_peak_time = 0.0

    def compute(self, setpoint: float, current: float) -> float:
        """حساب خرج PID"""
        now = time.time()
        dt = now - self._prev_time
        if dt <= 0:
            dt = 0.001

        error = setpoint - current
        self._error_history.append(error)

        # Proportional
        p = self.kp * error

        # Integral (with anti-windup)
        self._integral += error * dt
        self._integral = max(self.output_min / self.ki if self.ki != 0 else -1e9,
                            min(self.output_max / self.ki if self.ki != 0 else 1e9,
                                self._integral))
        i = self.ki * self._integral

        # Derivative
        d = self.kd * (error - self._prev_error) / dt if dt > 0 else 0

        output = p + i + d
        output = max(self.output_min, min(self.output_max, output))

        self._prev_error = error
        self._prev_time = now
        return output

    def auto_tune(self, setpoint: float, measure_fn: Callable, cycles: int = 10) -> Dict:
        """
        Ziegler-Nichols Auto-Tuning
        يضبط kp, ki, kd تلقائياً عبر اكتشاف نقطة الاهتزاز
        """
        print(f"[AI-PID] بدء Auto-Tune لـ '{self.name}'...")
        peaks = []
        valleys = []
        step_output = (self.output_max - self.output_min) * 0.5
        relay_output = step_output

        prev_error = setpoint - measure_fn()
        for i in range(cycles * 50):
            current = measure_fn()
            error = setpoint - current

            # Relay feedback
            if error > 0:
                output = relay_output
            else:
                output = -relay_output

            # كشف الإشارات
            if prev_error < 0 <= error:
                peaks.append(time.time())
            elif prev_error > 0 >= error:
                valleys.append(time.time())

            prev_error = error
            time.sleep(0.02)

        # حساب المعاملات من Ziegler-Nichols
        if len(peaks) >= 2:
            periods = [peaks[i+1] - peaks[i] for i in range(len(peaks)-1)]
            Tu = sum(periods) / len(periods)  # Ultimate period
            Ku = 4 * relay_output / (math.pi * relay_output)  # Ultimate gain

            # PID rules
            self.kp = 0.6 * Ku
            self.ki = 1.2 * Ku / Tu
            self.kd = 0.075 * Ku * Tu

            result = {"kp": self.kp, "ki": self.ki, "kd": self.kd, "Tu": Tu, "Ku": Ku}
            print(f"[AI-PID] Auto-Tune مكتمل: Kp={self.kp:.3f}, Ki={self.ki:.3f}, Kd={self.kd:.3f}")
            return result

        return {"kp": self.kp, "ki": self.ki, "kd": self.kd}

    def reset(self):
        """إعادة تعيين الحالة"""
        self._prev_error = 0.0
        self._integral = 0.0
        self._prev_time = time.time()

    def get_stats(self) -> Dict:
        """إحصائيات الأداء"""
        errors = list(self._error_history)
        if not errors:
            return {}
        return {
            "mean_error": sum(errors) / len(errors),
            "max_error": max(abs(e) for e in errors),
            "rms_error": math.sqrt(sum(e**2 for e in errors) / len(errors)),
            "stability": 1.0 - min(1.0, sum(abs(e) for e in errors) / (len(errors) * 100))
        }


# ─────────────────────────────────────────────────────────────
# 2. FUZZY LOGIC CONTROLLER
# ─────────────────────────────────────────────────────────────

class FuzzySet:
    """مجموعة ضبابية مثلثية"""
    def __init__(self, name: str, a: float, b: float, c: float):
        self.name = name
        self.a = a  # بداية
        self.b = b  # قمة
        self.c = c  # نهاية

    def membership(self, x: float) -> float:
        """درجة الانتماء"""
        if x <= self.a or x >= self.c:
            return 0.0
        elif self.a < x <= self.b:
            return (x - self.a) / (self.b - self.a)
        else:
            return (self.c - x) / (self.c - self.b)


class FuzzyController:
    """
    متحكم Fuzzy Logic للتحكم التكيفي في حركة الروبوت
    يستخدم لتجنب العقبات وتعديل السرعة تلقائياً
    """

    def __init__(self):
        # مجموعات المسافة (سم)
        self.distance_sets = {
            "near":   FuzzySet("near",   0,   0,  30),
            "medium": FuzzySet("medium", 20,  50,  80),
            "far":    FuzzySet("far",    70, 150, 150),
        }

        # مجموعات السرعة (-255 إلى 255)
        self.speed_sets = {
            "stop":   FuzzySet("stop",   -10,   0,  10),
            "slow":   FuzzySet("slow",    30,  80, 100),
            "medium": FuzzySet("medium",  80, 150, 200),
            "fast":   FuzzySet("fast",   150, 255, 255),
        }

        # قواعد (distance → speed)
        self.rules = {
            "near":   "stop",
            "medium": "slow",
            "far":    "fast",
        }

    def infer(self, distance: float) -> float:
        """استنتاج السرعة من المسافة"""
        # Fuzzification
        memberships = {name: s.membership(distance)
                      for name, s in self.distance_sets.items()}

        # Inference
        output_weights = {}
        for dist_name, mem in memberships.items():
            if mem > 0 and dist_name in self.rules:
                speed_name = self.rules[dist_name]
                output_weights[speed_name] = max(output_weights.get(speed_name, 0), mem)

        # Defuzzification (Center of Gravity)
        numerator = 0.0
        denominator = 0.0

        for speed_name, weight in output_weights.items():
            if speed_name in self.speed_sets:
                centroid = self.speed_sets[speed_name].b
                numerator += weight * centroid
                denominator += weight

        if denominator == 0:
            return 0.0
        return numerator / denominator

    def add_rule(self, distance_name: str, speed_name: str):
        """إضافة قاعدة مخصصة"""
        self.rules[distance_name] = speed_name


# ─────────────────────────────────────────────────────────────
# 3. REINFORCEMENT LEARNING (Q-LEARNING)
# ─────────────────────────────────────────────────────────────

class QLearningAgent:
    """
    وكيل تعلم معزز (Q-Learning)
    يتعلم الروبوت من تجاربه لاتخاذ أفضل قرار
    """

    def __init__(self, n_states: int = 10, n_actions: int = 4,
                 learning_rate: float = 0.1, discount: float = 0.9,
                 epsilon: float = 0.3):
        self.n_states = n_states
        self.n_actions = n_actions
        self.lr = learning_rate
        self.gamma = discount
        self.epsilon = epsilon
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995

        # Q-Table
        self.q_table: List[List[float]] = [
            [0.0] * n_actions for _ in range(n_states)
        ]
        self.episode = 0
        self.total_reward = 0.0
        self.action_names = {
            0: "FORWARD",
            1: "BACKWARD",
            2: "LEFT",
            3: "RIGHT"
        }

    def choose_action(self, state: int) -> int:
        """اختيار فعل (epsilon-greedy)"""
        if random.random() < self.epsilon:
            return random.randint(0, self.n_actions - 1)  # استكشاف
        return self.q_table[state].index(max(self.q_table[state]))  # استغلال

    def learn(self, state: int, action: int, reward: float, next_state: int):
        """تحديث Q-Table"""
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state])
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state][action] = new_q
        self.total_reward += reward

        # تقليل الاستكشاف مع الوقت
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def discretize_state(self, sensor_value: float, max_val: float = 200.0) -> int:
        """تحويل قيمة مستمرة إلى حالة رقمية"""
        normalized = max(0.0, min(1.0, sensor_value / max_val))
        return int(normalized * (self.n_states - 1))

    def save(self, filepath: str):
        """حفظ Q-Table"""
        with open(filepath, "w") as f:
            json.dump({"q_table": self.q_table, "epsilon": self.epsilon,
                      "episode": self.episode}, f, indent=2)
        print(f"[AI-RL] تم حفظ النموذج في {filepath}")

    def load(self, filepath: str) -> bool:
        """تحميل Q-Table"""
        try:
            with open(filepath) as f:
                data = json.load(f)
            self.q_table = data["q_table"]
            self.epsilon = data["epsilon"]
            self.episode = data["episode"]
            print(f"[AI-RL] تم تحميل النموذج من {filepath}")
            return True
        except FileNotFoundError:
            return False

    def get_policy(self) -> List[str]:
        """السياسة الحالية: أفضل فعل لكل حالة"""
        policy = []
        for state in range(self.n_states):
            best = self.q_table[state].index(max(self.q_table[state]))
            policy.append(self.action_names.get(best, str(best)))
        return policy


# ─────────────────────────────────────────────────────────────
# 4. ANOMALY DETECTION
# ─────────────────────────────────────────────────────────────

class AnomalyDetector:
    """
    كشف الشذوذ في بيانات المستشعرات
    يُنبّه عند وجود قراءات غير طبيعية
    """

    def __init__(self, window_size: int = 50, threshold_sigma: float = 3.0):
        self.window = deque(maxlen=window_size)
        self.threshold_sigma = threshold_sigma
        self.anomaly_count = 0
        self.total_samples = 0
        self.callbacks: List[Callable] = []

    def add_sample(self, value: float) -> bool:
        """إضافة قيمة جديدة وفحص الشذوذ"""
        self.total_samples += 1
        self.window.append(value)

        if len(self.window) < 5:
            return False

        mean = sum(self.window) / len(self.window)
        variance = sum((x - mean) ** 2 for x in self.window) / len(self.window)
        std = math.sqrt(variance) if variance > 0 else 1e-9

        z_score = abs(value - mean) / std
        is_anomaly = z_score > self.threshold_sigma

        if is_anomaly:
            self.anomaly_count += 1
            for cb in self.callbacks:
                cb(value, z_score, mean, std)

        return is_anomaly

    def on_anomaly(self, callback: Callable):
        """تسجيل callback عند الشذوذ"""
        self.callbacks.append(callback)

    def get_stats(self) -> Dict:
        """إحصائيات"""
        if not self.window:
            return {}
        values = list(self.window)
        mean = sum(values) / len(values)
        return {
            "mean": mean,
            "std": math.sqrt(sum((x - mean)**2 for x in values) / len(values)),
            "min": min(values),
            "max": max(values),
            "anomaly_rate": self.anomaly_count / max(self.total_samples, 1)
        }


# ─────────────────────────────────────────────────────────────
# 5. PATH PLANNING (A* ALGORITHM)
# ─────────────────────────────────────────────────────────────

@dataclass(order=True)
class AStarNode:
    f: float
    g: float = field(compare=False)
    h: float = field(compare=False)
    pos: Tuple[int, int] = field(compare=False)
    parent: Any = field(compare=False, default=None)


class AStarPlanner:
    """
    خوارزمية A* لتخطيط المسار
    تجد أقصر مسار في شبكة مع تجنب العقبات
    """

    def __init__(self, grid_width: int = 20, grid_height: int = 20):
        self.width = grid_width
        self.height = grid_height
        self.grid: List[List[int]] = [[0] * grid_width for _ in range(grid_height)]

    def set_obstacle(self, x: int, y: int):
        """وضع عقبة"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = 1

    def clear_obstacle(self, x: int, y: int):
        """إزالة عقبة"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = 0

    def _heuristic(self, a: Tuple, b: Tuple) -> float:
        return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

    def find_path(self, start: Tuple[int,int], goal: Tuple[int,int]) -> Optional[List[Tuple]]:
        """إيجاد المسار الأمثل"""
        if self.grid[start[1]][start[0]] or self.grid[goal[1]][goal[0]]:
            return None

        open_list: List[AStarNode] = []
        closed_set = set()

        start_node = AStarNode(
            f=0, g=0,
            h=self._heuristic(start, goal),
            pos=start
        )
        start_node.f = start_node.h
        open_list.append(start_node)

        node_map: Dict[Tuple, AStarNode] = {start: start_node}

        directions = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
        costs =      [1.0,  1.0,  1.0,  1.0,   1.414,1.414, 1.414, 1.414]

        while open_list:
            open_list.sort()
            current = open_list.pop(0)

            if current.pos == goal:
                # إعادة بناء المسار
                path = []
                node = current
                while node:
                    path.append(node.pos)
                    node = node.parent
                return list(reversed(path))

            closed_set.add(current.pos)

            for (dx, dy), cost in zip(directions, costs):
                nx, ny = current.pos[0] + dx, current.pos[1] + dy
                neighbor = (nx, ny)

                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                if self.grid[ny][nx] or neighbor in closed_set:
                    continue

                g = current.g + cost
                h = self._heuristic(neighbor, goal)
                f = g + h

                if neighbor in node_map and node_map[neighbor].g <= g:
                    continue

                node = AStarNode(f=f, g=g, h=h, pos=neighbor, parent=current)
                node_map[neighbor] = node
                open_list.append(node)

        return None  # لا يوجد مسار

    def print_grid(self, path: List[Tuple] = None, start=None, goal=None):
        """طباعة الشبكة مرئياً"""
        path_set = set(path) if path else set()
        lines = []
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                pos = (x, y)
                if pos == start:
                    row += "S "
                elif pos == goal:
                    row += "G "
                elif pos in path_set:
                    row += "· "
                elif self.grid[y][x]:
                    row += "█ "
                else:
                    row += "  "
            lines.append(row)
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# 6. LIGHTWEIGHT NEURAL NETWORK
# ─────────────────────────────────────────────────────────────

class NeuralNetwork:
    """
    شبكة عصبية خفيفة الوزن بدون مكتبات خارجية
    مناسبة للأنظمة المدمجة
    تستخدم لتصنيف حالات الروبوت
    """

    def __init__(self, layers: List[int]):
        """
        layers: قائمة بأحجام الطبقات
        مثال: [4, 8, 4, 3] = 4 مدخلات, طبقتين مخفيتين, 3 مخرجات
        """
        self.layers = layers
        self.weights: List[List[List[float]]] = []
        self.biases: List[List[float]] = []
        self._init_weights()
        self.loss_history: List[float] = []

    def _init_weights(self):
        """تهيئة الأوزان (Xavier initialization)"""
        for i in range(len(self.layers) - 1):
            n_in = self.layers[i]
            n_out = self.layers[i + 1]
            scale = math.sqrt(2.0 / n_in)
            W = [[random.gauss(0, scale) for _ in range(n_in)] for _ in range(n_out)]
            b = [0.0] * n_out
            self.weights.append(W)
            self.biases.append(b)

    @staticmethod
    def _relu(x: float) -> float:
        return max(0.0, x)

    @staticmethod
    def _relu_grad(x: float) -> float:
        return 1.0 if x > 0 else 0.0

    @staticmethod
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-max(-500, min(500, x))))

    @staticmethod
    def _softmax(vec: List[float]) -> List[float]:
        max_v = max(vec)
        exp_v = [math.exp(x - max_v) for x in vec]
        total = sum(exp_v)
        return [e / total for e in exp_v]

    def forward(self, inputs: List[float]) -> List[float]:
        """تمرير للأمام"""
        self._activations = [inputs]
        self._pre_activations = []

        current = inputs
        for i, (W, b) in enumerate(zip(self.weights, self.biases)):
            pre = [sum(W[j][k] * current[k] for k in range(len(current))) + b[j]
                   for j in range(len(W))]
            self._pre_activations.append(pre)

            if i < len(self.weights) - 1:
                current = [self._relu(x) for x in pre]
            else:
                current = self._softmax(pre)
            self._activations.append(current)

        return current

    def predict(self, inputs: List[float]) -> int:
        """التنبؤ بالصنف"""
        output = self.forward(inputs)
        return output.index(max(output))

    def train_step(self, inputs: List[float], target_class: int,
                   learning_rate: float = 0.01) -> float:
        """خطوة تدريب واحدة (backpropagation)"""
        output = self.forward(inputs)

        # Cross-entropy loss
        loss = -math.log(max(output[target_class], 1e-9))
        self.loss_history.append(loss)

        # Gradient للمخرج
        n_out = len(output)
        delta = [output[i] - (1.0 if i == target_class else 0.0) for i in range(n_out)]

        # Backpropagation
        for layer in range(len(self.weights) - 1, -1, -1):
            W = self.weights[layer]
            b = self.biases[layer]
            act = self._activations[layer]

            # تحديث الأوزان
            n_out_l = len(W)
            n_in_l = len(W[0])
            for j in range(n_out_l):
                for k in range(n_in_l):
                    W[j][k] -= learning_rate * delta[j] * act[k]
                b[j] -= learning_rate * delta[j]

            if layer > 0:
                new_delta = [0.0] * n_in_l
                for k in range(n_in_l):
                    s = sum(W[j][k] * delta[j] for j in range(n_out_l))
                    new_delta[k] = s * self._relu_grad(self._pre_activations[layer-1][k])
                delta = new_delta

        return loss

    def train(self, dataset: List[Tuple[List[float], int]],
              epochs: int = 100, lr: float = 0.01) -> List[float]:
        """تدريب كامل"""
        epoch_losses = []
        for epoch in range(epochs):
            random.shuffle(dataset)
            total_loss = 0.0
            for inputs, label in dataset:
                loss = self.train_step(inputs, label, lr)
                total_loss += loss
            avg_loss = total_loss / len(dataset)
            epoch_losses.append(avg_loss)
            if epoch % 10 == 0:
                print(f"[AI-NN] Epoch {epoch}/{epochs} — Loss: {avg_loss:.4f}")
        return epoch_losses


# ─────────────────────────────────────────────────────────────
# 7. GESTURE RECOGNITION (IMU-BASED)
# ─────────────────────────────────────────────────────────────

class GestureRecognizer:
    """
    التعرف على الإيماءات من بيانات IMU (Accelerometer + Gyroscope)
    يُستخدم للتحكم بالروبوت باليد
    """

    GESTURES = {
        "shake":      {"accel_peak": 3.0,  "gyro_peak": 0.0,  "duration": 0.3},
        "tilt_left":  {"accel_peak": 0.0,  "gyro_peak": 90.0, "duration": 0.2},
        "tilt_right": {"accel_peak": 0.0,  "gyro_peak": -90.0,"duration": 0.2},
        "tap":        {"accel_peak": 2.0,  "gyro_peak": 0.0,  "duration": 0.1},
        "rotate":     {"accel_peak": 0.0,  "gyro_peak": 180.0,"duration": 0.5},
    }

    def __init__(self, sample_rate: int = 50):
        self.sample_rate = sample_rate
        self.window: deque = deque(maxlen=sample_rate * 2)
        self.detected_gestures: List[Dict] = []

    def add_sample(self, ax: float, ay: float, az: float,
                   gx: float, gy: float, gz: float):
        """إضافة عينة IMU"""
        accel_mag = math.sqrt(ax**2 + ay**2 + az**2)
        gyro_mag = math.sqrt(gx**2 + gy**2 + gz**2)
        self.window.append({
            "accel": accel_mag, "gyro": gyro_mag,
            "ax": ax, "ay": ay, "az": az,
            "gx": gx, "gy": gy, "gz": gz,
            "time": time.time()
        })
        return self._detect()

    def _detect(self) -> Optional[str]:
        """محاولة كشف إيماءة"""
        if len(self.window) < 5:
            return None

        recent = list(self.window)[-10:]
        max_accel = max(s["accel"] for s in recent)
        max_gyro = max(abs(s["gyro"]) for s in recent)
        avg_gx = sum(s["gx"] for s in recent) / len(recent)

        # Shake
        if max_accel > 2.5:
            return self._register_gesture("shake")

        # Tilt
        if avg_gx > 60:
            return self._register_gesture("tilt_left")
        elif avg_gx < -60:
            return self._register_gesture("tilt_right")

        # Rotation
        if max_gyro > 150:
            return self._register_gesture("rotate")

        return None

    def _register_gesture(self, name: str) -> str:
        """تسجيل إيماءة مكتشفة"""
        last = [g["name"] for g in self.detected_gestures[-3:]] if self.detected_gestures else []
        if name in last:
            return name  # تجنب التكرار
        self.detected_gestures.append({"name": name, "time": time.time()})
        print(f"[AI-GESTURE] 🤚 تم كشف إيماءة: {name}")
        return name


# ─────────────────────────────────────────────────────────────
# 8. AI COORDINATOR — يجمع كل الأنظمة معاً
# ─────────────────────────────────────────────────────────────

class RoboAI:
    """
    منسق الذكاء الاصطناعي الكامل لـ RoboOS
    يدير جميع أنظمة الـ AI ويربطها بالروبوت
    """

    def __init__(self, name: str = "RoboAI"):
        self.name = name
        self.version = "2.0"

        # تهيئة جميع أنظمة AI
        self.motion_pid = PIDController(kp=2.0, ki=0.1, kd=0.05, name="Motion")
        self.balance_pid = PIDController(kp=5.0, ki=0.5, kd=0.2, name="Balance")
        self.fuzzy = FuzzyController()
        self.rl_agent = QLearningAgent(n_states=16, n_actions=4)
        self.anomaly_detector = AnomalyDetector(window_size=50, threshold_sigma=3.0)
        self.path_planner = AStarPlanner(grid_width=20, grid_height=20)
        self.neural_net = NeuralNetwork(layers=[6, 12, 8, 4])
        self.gesture = GestureRecognizer()

        # إحصائيات
        self.decisions_made = 0
        self.start_time = time.time()
        self.ai_log: deque = deque(maxlen=500)

        # تسجيل كشف الشذوذ
        self.anomaly_detector.on_anomaly(self._on_anomaly)

        print(f"[{self.name}] ✅ تم تهيئة نظام AI v{self.version}")

    def _on_anomaly(self, value: float, z_score: float, mean: float, std: float):
        """معالجة الشذوذ"""
        msg = f"⚠️ شذوذ في المستشعر: قيمة={value:.2f}, Z={z_score:.2f} (μ={mean:.2f}±{std:.2f})"
        self.ai_log.append({"type": "anomaly", "msg": msg, "time": time.time()})
        print(f"[AI-ANOMALY] {msg}")

    def decide_speed(self, sensor_distance: float) -> float:
        """اتخاذ قرار السرعة بناءً على المستشعر"""
        self.decisions_made += 1

        # Fuzzy اتخاذ قرار أولي
        speed = self.fuzzy.infer(sensor_distance)

        # كشف الشذوذ
        self.anomaly_detector.add_sample(sensor_distance)

        # Q-Learning تعلم
        state = self.rl_agent.discretize_state(sensor_distance)
        action = self.rl_agent.choose_action(state)
        reward = sensor_distance / 100.0  # مكافأة على البعد
        self.rl_agent.learn(state, action, reward, state)

        self.ai_log.append({
            "type": "decision",
            "sensor": sensor_distance,
            "speed": speed,
            "time": time.time()
        })

        return speed

    def navigate_to(self, current: Tuple[int,int], goal: Tuple[int,int],
                    obstacles: List[Tuple[int,int]] = None) -> Optional[List[Tuple]]:
        """تخطيط المسار إلى الهدف"""
        # مسح وإضافة العقبات
        self.path_planner.grid = [[0] * self.path_planner.width
                                  for _ in range(self.path_planner.height)]
        if obstacles:
            for obs in obstacles:
                self.path_planner.set_obstacle(obs[0], obs[1])

        path = self.path_planner.find_path(current, goal)
        if path:
            print(f"[AI-PATH] ✅ مسار موجود: {len(path)} نقطة")
        else:
            print(f"[AI-PATH] ❌ لا يوجد مسار")
        return path

    def classify_state(self, sensor_data: List[float]) -> str:
        """تصنيف حالة الروبوت بالشبكة العصبية"""
        if len(sensor_data) != self.neural_net.layers[0]:
            sensor_data = (sensor_data + [0.0] * self.neural_net.layers[0])[:self.neural_net.layers[0]]
        prediction = self.neural_net.predict(sensor_data)
        states = ["NORMAL", "OBSTACLE", "STUCK", "RECOVERY"]
        return states[prediction % len(states)]

    def process_imu(self, ax, ay, az, gx, gy, gz) -> Optional[str]:
        """معالجة بيانات IMU وكشف الإيماءات"""
        return self.gesture.add_sample(ax, ay, az, gx, gy, gz)

    def control_motor(self, target: float, current: float) -> float:
        """تحكم PID في المحرك"""
        return self.motion_pid.compute(target, current)

    def get_status(self) -> Dict:
        """تقرير حالة الـ AI"""
        uptime = time.time() - self.start_time
        pid_stats = self.motion_pid.get_stats()
        anomaly_stats = self.anomaly_detector.get_stats()
        policy = self.rl_agent.get_policy()

        return {
            "name": self.name,
            "version": self.version,
            "uptime_s": round(uptime, 2),
            "decisions_made": self.decisions_made,
            "pid": pid_stats,
            "anomaly": anomaly_stats,
            "rl_epsilon": round(self.rl_agent.epsilon, 4),
            "rl_total_reward": round(self.rl_agent.total_reward, 2),
            "rl_policy": policy,
            "log_size": len(self.ai_log)
        }

    def print_status(self):
        """طباعة تقرير مفصل"""
        s = self.get_status()
        print(f"""
╔══════════════════════════════════════════════════════╗
║             RoboOS AI Status Report                  ║
║  {s['name']} v{s['version']}                                    ║
╠══════════════════════════════════════════════════════╣
║  وقت التشغيل:     {s['uptime_s']:.1f}s                           ║
║  القرارات:        {s['decisions_made']}                               ║
║  مكافأة RL:       {s['rl_total_reward']:.2f}                          ║
║  Epsilon (RL):    {s['rl_epsilon']:.4f}                           ║
╠══════════════════════════════════════════════════════╣
║  سجل الـ AI:      {s['log_size']} مدخل                            ║
╚══════════════════════════════════════════════════════╝""")


# ─────────────────────────────────────────────────────────────
# FACTORY FUNCTION
# ─────────────────────────────────────────────────────────────

_ai_instance: Optional[RoboAI] = None

def get_ai(name: str = "RoboAI") -> RoboAI:
    """الحصول على نسخة AI عامة (Singleton)"""
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = RoboAI(name)
    return _ai_instance
