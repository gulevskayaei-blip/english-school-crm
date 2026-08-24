<template>
  <div class="level-test">
    <!-- Заголовок -->
    <div class="test-header" v-if="!testStarted && !testFinished">
      <h1>📝 Определите свой уровень английского</h1>
      <p>Выберите подходящий тест</p>
    </div>

    <!-- Выбор теста -->
    <div v-if="!testStarted && !testFinished" class="test-selection">
      <div class="test-card young" @click="startTest('young')">
        <div class="test-emoji">🧒</div>
        <h2>Для детей 7-12 лет</h2>
        <p>45 вопросов • 30-40 минут</p>
        <span class="test-badge">Young Learners</span>
      </div>
      <div class="test-card adult" @click="startTest('adult')">
        <div class="test-emoji">👨‍🎓</div>
        <h2>Для подростков и взрослых</h2>
        <p>80 вопросов • 30-40 минут</p>
        <span class="test-badge">Upstream/Enterprise</span>
      </div>
    </div>

    <!-- Прогресс-бар -->
    <div class="progress-bar" v-if="testStarted && !testFinished">
      <div class="progress" :style="{ width: (currentQuestion / totalQuestions) * 100 + '%' }"></div>
      <span>{{ currentQuestion }} / {{ totalQuestions }}</span>
    </div>

    <!-- Вопросы -->
    <div v-if="testStarted && !testFinished" class="question-card">
      <div class="question-number">Вопрос {{ currentQuestion }} из {{ totalQuestions }}</div>
      <h3>{{ currentQuestionData.question }}</h3>
      
      <div class="answers" v-if="currentQuestionData.answers">
        <div 
          v-for="(answer, index) in currentQuestionData.answers" 
          :key="index"
          class="answer-btn"
          :class="{ selected: selectedAnswer === index }"
          @click="selectAnswer(index)"
        >
          <span class="answer-letter">{{ ['A', 'B', 'C', 'D'][index] }}</span>
          {{ answer }}
        </div>
      </div>

      <div class="answers" v-else>
        <input 
          v-model="writtenAnswer" 
          placeholder="Введите ответ" 
          class="written-input"
          @keyup.enter="nextQuestion"
        />
      </div>

      <button 
        class="next-btn" 
        :disabled="selectedAnswer === null && !writtenAnswer"
        @click="nextQuestion"
      >
        {{ currentQuestion === totalQuestions ? 'Узнать результат' : 'Далее →' }}
      </button>
    </div>

    <!-- Результат -->
    <div v-if="testFinished" class="result-card">
      <div class="result-emoji">{{ resultEmoji }}</div>
      <h2>{{ resultText }}</h2>
      <div class="score-display">
        <div class="score-circle">
          <span class="score-number">{{ score }}</span>
          <span class="score-total">/ {{ totalQuestions }}</span>
        </div>
      </div>
      <p class="result-description">{{ resultDescription }}</p>
      <div class="level-bar">
        <div class="level-fill" :style="{ width: levelPercentage + '%' }"></div>
      </div>
      <div class="level-labels">
        <span>{{ testType === 'young' ? 'Starter' : 'Beginner' }}</span>
        <span>{{ testType === 'young' ? 'Intermediate' : 'Advanced' }}</span>
      </div>
      
      <div class="result-actions">
        <button class="btn-primary" @click="$router.push('/booking')">
          Записаться на занятие
        </button>
        <button class="btn-secondary" @click="restartTest">
          Пройти тест заново
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LevelTest',
  data() {
    return {
      testType: null,
      testStarted: false,
      testFinished: false,
      currentQuestion: 1,
      selectedAnswer: null,
      writtenAnswer: '',
      userAnswers: [],
      youngQuestions: [],
      adultQuestions: [],
    }
  },
  computed: {
    totalQuestions() {
      return this.testType === 'young' ? 45 : 80
    },
    currentQuestions() {
      return this.testType === 'young' ? this.youngQuestions : this.adultQuestions
    },
    currentQuestionData() {
      return this.currentQuestions[this.currentQuestion - 1] || {}
    },
    score() {
      return this.userAnswers.filter((a, i) => {
        const correct = this.currentQuestions[i]?.correct
        if (typeof correct === 'number') return a === correct
        if (typeof correct === 'string') return a?.toString().toLowerCase().trim() === correct.toLowerCase().trim()
        return false
      }).length
    },
    resultText() {
      if (this.testType === 'young') return this.getYoungLevel()
      return this.getAdultLevel()
    },
    resultEmoji() {
      const p = this.levelPercentage
      if (p < 25) return '🌱'
      if (p < 50) return '🌿'
      if (p < 75) return '🌳'
      if (p < 90) return '🎯'
      return '🏆'
    },
    resultDescription() {
      if (this.testType === 'young') return this.getYoungDescription()
      return this.getAdultDescription()
    },
    levelPercentage() {
      return (this.score / this.totalQuestions) * 100
    },
  },
  mounted() {
    this.initYoungTest()
    this.initAdultTest()
  },
  methods: {
    initYoungTest() {
      this.youngQuestions = [
        { question: 'When _______ your birthday?', answers: ['are', 'does', 'is'], correct: 2 },
        { question: 'Who is _______ the picture?', answers: ['in', 'at', 'on'], correct: 0 },
        { question: 'How many chairs _______ in the room?', answers: ['are there', 'is there', 'there are'], correct: 0 },
        { question: '_______ a cup of tea? - Yes, I would.', answers: ['Do you like', 'Would you like', 'Would you want'], correct: 1 },
        { question: 'Where do people have breakfast?', answers: ['in the living room', 'in the bedroom', 'in the dining room'], correct: 2 },
        { question: 'Write the plural: a mouse →', answers: null, correct: 'mice' },
        { question: 'Write the plural: a man →', answers: null, correct: 'men' },
        { question: 'Write the plural: a lemon →', answers: null, correct: 'lemons' },
        { question: 'Write the plural: a sheep →', answers: null, correct: 'sheep' },
        { question: '_______ boat is it?', answers: ['Which', 'Whose', 'Who'], correct: 1 },
        { question: 'Which animals give milk? (2 answers)', answers: ['goats', 'lions', 'bears', 'cows'], correct: 0 },
        { question: 'How many fingers do you have on your hand?', answers: null, correct: '5' },
        { question: 'I like _______ music.', answers: ['listening to', 'hearing to', 'hearing'], correct: 0 },
        { question: 'Who lives in the water?', answers: ['a hippo', 'a butterfly', 'a snake'], correct: 0 },
        { question: 'Where is Jill? She is _______ you.', answers: ['in front of', 'on', 'behind'], correct: 2 },
        { question: '_______ toys are old.', answers: ['These', 'This', 'That'], correct: 0 },
        { question: 'Can you _______ a bicycle?', answers: ['drive', 'play', 'ride'], correct: 2 },
        { question: 'Whose pencil is this? This is _______.', answers: ['my', 'me', 'mine'], correct: 2 },
        { question: 'Mary\'s hair isn\'t short, it\'s _______.', answers: null, correct: 'long' },
        { question: 'At school we _______ throw things.', answers: ['must', 'can\'t', 'mustn\'t'], correct: 2 },
        { question: 'What did you buy yesterday? I _______ new shoes.', answers: ['baught', 'bought', 'did buy'], correct: 1 },
        { question: 'Write the plural: a leaf →', answers: null, correct: 'leaves' },
        { question: 'Write the plural: a tooth →', answers: null, correct: 'teeth' },
        { question: 'Write the plural: an apple →', answers: null, correct: 'apples' },
        { question: 'What day was it yesterday? (Today is Wednesday)', answers: null, correct: 'tuesday' },
        { question: 'Travelling to Thailand was _______ trip.', answers: ['better', 'the best', 'best'], correct: 1 },
        { question: '_______ I help you carry the bags, Mum?', answers: ['Will', 'Should', 'Shall'], correct: 2 },
        { question: 'Did you go to the zoo? Yes, I _______.', answers: null, correct: 'did' },
        { question: 'Choose the correct:', answers: ['They never don\'t eat sweets', 'They never eat sweets', 'They never eats sweets'], correct: 1 },
        { question: 'My brother is _______ than me.', answers: ['fatter', 'faster', 'taller', 'younger'], correct: 2 },
        { question: '_______ cat is black with a white tail.', answers: ['a', 'the', '—'], correct: 1 },
        { question: 'Do you want to _______ to the cinema?', answers: null, correct: 'go' },
        { question: '_______ is Jim crying?', answers: ['Why', 'What', 'When'], correct: 0 },
        { question: 'My cousin is good _______ fishing.', answers: ['at', 'in', 'on'], correct: 0 },
        { question: 'What\'s your favourite subject?', answers: null, correct: '' },
        { question: 'The sweater is made of _______.', answers: ['wood', 'wool', 'paper'], correct: 1 },
        { question: 'Can you play _______ guitar?', answers: ['the', 'a', '—'], correct: 0 },
        { question: 'Name three winter months:', answers: null, correct: 'december' },
        { question: 'I don\'t know _______ about him.', answers: ['everything', 'nothing', 'anything'], correct: 2 },
        { question: 'Past form of "to meet":', answers: null, correct: 'met' },
        { question: 'Past form of "to see":', answers: null, correct: 'saw' },
        { question: '_______ you ever _______ to Spain?', answers: null, correct: 'have been' },
        { question: 'I haven\'t seen the movie _______.', answers: ['already', 'just', 'yet'], correct: 2 },
        { question: 'I _______ when I saw her.', answers: ['was crossing the street', 'crossed the street', 'were crossing'], correct: 0 },
        { question: 'My sister is _______ than me.', answers: ['more beautiful', 'cleverer', 'taller', 'faster'], correct: 1 },
      ]
    },
    initAdultTest() {
      this.adultQuestions = [
        { question: 'Ann ....... shopping every day.', answers: ['is going', 'goes', 'go', 'has gone'], correct: 1 },
        { question: 'Frank and Henry ....... tennis now.', answers: ['are playing', 'play', 'were playing', 'played'], correct: 0 },
        { question: 'We haven\'t got ....... apples.', answers: ['no', 'some', 'any', 'much'], correct: 2 },
        { question: '"....... I watch TV now?" "No, clean up first."', answers: ['Must', 'Should', 'Can', 'Do'], correct: 2 },
        { question: 'I\'d like a ....... of milk, please.', answers: ['bar', 'box', 'carton', 'packet'], correct: 2 },
        { question: 'Betty is ....... than Jane.', answers: ['taller', 'the tallest', 'as tall', 'not as tall'], correct: 0 },
        { question: 'There is a red car. ....... car belongs to my friend.', answers: ['The', 'A', 'Some', 'Any'], correct: 0 },
        { question: '....... touch the iron. It\'s very hot.', answers: ['Can\'t', 'Don\'t', 'Shouldn\'t', 'Didn\'t'], correct: 1 },
        { question: 'There ....... a lot of people last night.', answers: ['is', 'are', 'was', 'were'], correct: 3 },
        { question: '....... your jumper. It\'s a bit chilly.', answers: ['Take on', 'Take off', 'Put on', 'Put off'], correct: 2 },
        { question: 'My flat has central ....... so it\'s warm.', answers: ['heating', 'system', 'wardrobe', 'parking'], correct: 0 },
        { question: 'If you give somebody a drink, you say: "......."', answers: ['Please.', 'Not at all.', 'Here you are.', 'Thanks.'], correct: 2 },
        { question: '....... to my party tomorrow?', answers: ['Will you come', 'Did you come', 'Have you come', 'Do you come'], correct: 0 },
        { question: 'Look at the clouds! It ....... soon.', answers: ['is raining', 'was raining', 'is going to rain', 'has been raining'], correct: 2 },
        { question: 'She wasn\'t home when the telephone .......', answers: ['is ringing', 'rings', 'has rung', 'rang'], correct: 3 },
        { question: 'What was the weather .......?', answers: ['look', 'like', 'nice', 'good'], correct: 1 },
        { question: 'How do I ....... to the post office?', answers: ['get', 'walk', 'go', 'come'], correct: 0 },
        { question: 'He\'s an early bird. He ....... gets up late.', answers: ['always', 'usually', 'ever', 'seldom'], correct: 3 },
        { question: 'If you don\'t study, you ....... pass.', answers: ['don\'t', 'didn\'t', 'won\'t', 'wouldn\'t'], correct: 2 },
        { question: 'Jones is ....... of all the players.', answers: ['as short', 'not as short', 'much shorter', 'the shortest'], correct: 3 },
        { question: '"Thank you very much." "......."', answers: ['Very well.', 'Please.', 'Why not?', 'Don\'t mention it.'], correct: 3 },
        { question: '....... to London?', answers: ['Are you ever', 'Will you ever be', 'Have you ever been', 'Were you ever'], correct: 2 },
        { question: 'The window ....... by some boys yesterday.', answers: ['broke', 'was broken', 'had broken', 'had been broken'], correct: 1 },
        { question: 'Careful students do not ....... mistakes.', answers: ['do', 'have', 'get', 'make'], correct: 3 },
        { question: 'I attended ....... a boring lecture.', answers: ['too', 'as', 'so', 'such'], correct: 3 },
        { question: 'I ....... in the garden when it started to rain.', answers: ['worked', 'was working', 'had worked', 'have been working'], correct: 1 },
        { question: 'If you want something, you ask ....... it.', answers: ['for', 'from', 'on', 'about'], correct: 0 },
        { question: 'We ....... go in. It\'s a no-entry area.', answers: ['must', 'can', 'mustn\'t', 'needn\'t'], correct: 2 },
        { question: '"Why are you late?" "I ....... my bus."', answers: ['lost', 'spent', 'missed', 'escaped'], correct: 2 },
        { question: 'Janet has bought ....... pine furniture.', answers: ['a few', 'many', 'a number of', 'some'], correct: 3 },
        { question: 'Why don\'t you ....... us?', answers: ['meet', 'join', 'show', 'leave'], correct: 1 },
        { question: 'I like girls ....... are pretty.', answers: ['who', 'whom', 'which', 'whose'], correct: 0 },
        { question: 'John doesn\'t smoke, .......?', answers: ['is he', 'isn\'t he', 'does he', 'doesn\'t he'], correct: 2 },
        { question: 'He ....... drinks nor smokes.', answers: ['or', 'nor', 'either', 'neither'], correct: 3 },
        { question: 'Paul moved ....... last month.', answers: ['home', 'house', 'flat', 'room'], correct: 1 },
        { question: '....... has ever treated me like that!', answers: ['Someone', 'Everyone', 'Anyone', 'No one'], correct: 3 },
        { question: 'I ....... my dentist tomorrow.', answers: ['see', 'have seen', 'am seeing', 'will have seen'], correct: 2 },
        { question: 'Do you know what time .......?', answers: ['the film starts', 'does the film start', 'the film will start', 'will the film start'], correct: 0 },
        { question: 'If I had enough money, I ....... a bike.', answers: ['will buy', 'have bought', 'bought', 'would buy'], correct: 3 },
        { question: 'Weekly pay is called a .......', answers: ['perk', 'wage', 'salary', 'pension'], correct: 1 },
        { question: 'His mother doesn\'t let him ....... TV.', answers: ['to watch', 'watch', 'watching', 'to watching'], correct: 1 },
        { question: 'If you decline an offer, you turn it .......', answers: ['off', 'back', 'down', 'over'], correct: 2 },
        { question: '....... here long?', answers: ['Do you work', 'Are you working', 'Had you worked', 'Have you been working'], correct: 3 },
        { question: 'A challenging task is very .......', answers: ['easy', 'well-paid', 'urgent', 'demanding'], correct: 3 },
        { question: 'Barbara said she ....... to Poland next year.', answers: ['will return', 'would return', 'has returned', 'had returned'], correct: 1 },
        { question: 'It looks ....... rain.', answers: ['like', 'as', 'for', 'to'], correct: 0 },
        { question: 'Philip ....... going for a swim.', answers: ['offered', 'suggested', 'invited', 'asked'], correct: 1 },
        { question: 'I wish I ....... drive a car.', answers: ['can', 'can\'t', 'could', 'couldn\'t'], correct: 2 },
        { question: 'This time tomorrow we ....... to London.', answers: ['fly', 'are flying', 'will fly', 'will be flying'], correct: 3 },
        { question: 'He lives on the ....... of London.', answers: ['outside', 'outdoors', 'outskirts', 'outwards'], correct: 2 },
        { question: 'I\'ll never forget ....... her.', answers: ['to meet', 'meeting', 'have met', 'had met'], correct: 1 },
        { question: 'Take a jacket in case it ....... cold.', answers: ['gets', 'got', 'will get', 'has got'], correct: 0 },
        { question: 'He has a reputation for being ....... to employees.', answers: ['upset', 'furious', 'rude', 'annoyed'], correct: 2 },
        { question: 'He always ....... by the mechanics.', answers: ['repairs it', 'has repaired it', 'has it repaired', 'had it repaired'], correct: 2 },
        { question: 'I\'d rather we ....... until tomorrow.', answers: ['won\'t leave', 'don\'t leave', 'didn\'t leave', 'hadn\'t left'], correct: 2 },
        { question: 'Oxfam is ....... to helping the poor.', answers: ['qualified', 'committed', 'expert', 'trained'], correct: 1 },
        { question: 'Joanna ....... English for 3 years before she went.', answers: ['has studied', 'has been studying', 'was studying', 'had studied'], correct: 3 },
        { question: 'Richard is ....... enough for the job.', answers: ['old', 'not old', 'young', 'not young'], correct: 1 },
        { question: 'You ....... killed!', answers: ['would be', 'might be', 'could have been', 'must have been'], correct: 2 },
        { question: 'If a car pulls up, it .......', answers: ['stops', 'accelerates', 'drives off', 'slows down'], correct: 0 },
      ]
    },
    startTest(type) {
      this.testType = type
      this.testStarted = true
    },
    selectAnswer(index) {
      this.selectedAnswer = index
      this.writtenAnswer = ''
    },
    nextQuestion() {
      const answer = this.selectedAnswer !== null ? this.selectedAnswer : this.writtenAnswer
      this.userAnswers.push(answer)
      
      if (this.currentQuestion < this.totalQuestions) {
        this.currentQuestion++
        this.selectedAnswer = null
        this.writtenAnswer = ''
      } else {
        this.testFinished = true
        this.testStarted = false
      }
    },
    restartTest() {
      this.testType = null
      this.testStarted = false
      this.testFinished = false
      this.currentQuestion = 1
      this.selectedAnswer = null
      this.writtenAnswer = ''
      this.userAnswers = []
    },
    getYoungLevel() {
      const s = this.score
      if (s <= 14) return 'Starter'
      if (s <= 30) return 'Elementary (A1)'
      if (s <= 40) return 'Pre-Intermediate (A2)'
      return 'Intermediate (B1)'
    },
    getAdultLevel() {
      const s = this.score
      if (s <= 15) return 'Beginner (Enterprise 1)'
      if (s <= 30) return 'Elementary (Enterprise 2)'
      if (s <= 50) return 'Pre-Intermediate (Enterprise 3)'
      if (s <= 70) return 'Intermediate (Enterprise 4)'
      if (s <= 75) return 'Upper-Intermediate'
      return 'Advanced'
    },
    getYoungDescription() {
      const s = this.score
      if (s <= 14) return 'Базовые знания. Рекомендуем начальный курс с фокусом на словарный запас и простые предложения.'
      if (s <= 30) return 'Понимает простые выражения. Рекомендуем курс Elementary с акцентом на грамматику.'
      if (s <= 40) return 'Хороший уровень! Можно записаться в группы Pre-Intermediate.'
      return 'Отличный результат! Подойдут группы Intermediate.'
    },
    getAdultDescription() {
      const s = this.score
      if (s <= 15) return 'Начальный уровень. Рекомендуем курс для начинающих.'
      if (s <= 30) return 'Базовые знания. Подойдёт курс Elementary.'
      if (s <= 50) return 'Уверенный уровень. Рекомендуем Pre-Intermediate.'
      if (s <= 70) return 'Хороший английский! Подойдёт Intermediate.'
      if (s <= 75) return 'Продвинутый уровень. Рекомендуем Upper-Intermediate.'
      return 'Превосходно! Можно начинать Advanced курс.'
    },
  },
}
</script>

<style scoped>
.level-test {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', sans-serif;
}

.test-header {
  text-align: center;
  margin-bottom: 30px;
}

.test-header h1 {
  font-size: 28px;
  color: #2c3e50;
}

.test-selection {
  display: flex;
  gap: 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.test-card {
  flex: 1;
  min-width: 280px;
  max-width: 350px;
  padding: 30px;
  border-radius: 15px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid #e0e0e0;
}

.test-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
}

.test-card.young:hover {
  border-color: #ff9800;
}

.test-card.adult:hover {
  border-color: #42b983;
}

.test-emoji {
  font-size: 60px;
  margin-bottom: 15px;
}

.test-card h2 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.test-badge {
  display: inline-block;
  padding: 5px 15px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: bold;
  margin-top: 10px;
}

.young .test-badge {
  background: #fff3cd;
  color: #ff9800;
}

.adult .test-badge {
  background: #d4edda;
  color: #28a745;
}

.progress-bar {
  height: 30px;
  background: #e9ecef;
  border-radius: 15px;
  margin-bottom: 30px;
  position: relative;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #42b983, #38a169);
  transition: width 0.3s;
}

.progress-bar span {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-weight: bold;
}

.question-card {
  background: white;
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 2px 15px rgba(0,0,0,0.1);
}

.question-number {
  color: #999;
  margin-bottom: 15px;
}

.question-card h3 {
  font-size: 20px;
  margin-bottom: 25px;
  line-height: 1.5;
}

.answers {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.answer-btn {
  padding: 15px 20px;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
}

.answer-btn:hover {
  border-color: #42b983;
  background: #f0fff4;
}

.answer-btn.selected {
  border-color: #42b983;
  background: #d4edda;
}

.answer-letter {
  display: inline-block;
  width: 28px;
  height: 28px;
  line-height: 28px;
  text-align: center;
  background: #42b983;
  color: white;
  border-radius: 50%;
  margin-right: 10px;
  font-weight: bold;
  font-size: 14px;
}

.written-input {
  width: 100%;
  padding: 15px;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  font-size: 16px;
  box-sizing: border-box;
}

.next-btn {
  width: 100%;
  padding: 15px;
  margin-top: 25px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 18px;
  cursor: pointer;
}

.next-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.result-card {
  text-align: center;
  background: white;
  border-radius: 15px;
  padding: 40px;
  box-shadow: 0 2px 15px rgba(0,0,0,0.1);
}

.result-emoji {
  font-size: 80px;
  margin-bottom: 20px;
}

.result-card h2 {
  font-size: 28px;
  color: #2c3e50;
}

.score-display {
  margin: 20px 0;
}

.score-circle {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #42b983, #38a169);
  color: white;
}

.score-number {
  font-size: 36px;
  font-weight: bold;
}

.score-total {
  font-size: 14px;
}

.result-description {
  margin: 20px 0;
  color: #666;
  line-height: 1.6;
}

.level-bar {
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  margin: 20px 0 10px;
  overflow: hidden;
}

.level-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff9800, #42b983);
  transition: width 0.5s;
}

.level-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.result-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 30px;
}

.btn-primary {
  padding: 15px 30px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  cursor: pointer;
}

.btn-secondary {
  padding: 15px 30px;
  background: white;
  color: #42b983;
  border: 2px solid #42b983;
  border-radius: 10px;
  font-size: 16px;
  cursor: pointer;
}
</style>
