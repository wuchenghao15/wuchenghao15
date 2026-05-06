// 添加ES6+兼容性支持
if (typeof Promise === "undefined") {
    // 这里可以添加具体的polyfill代码
    console.warn("This browser requires a polyfill for ES6+ features");
}

/**
 * AI试题生成器
 * 根据用户日语等级向下兼容生成动态随机试题
 */

class AIQuestionGenerator {
    constructor() {
        this.questionTemplates = {
            vocabulary: [
                {
                    pattern: "{word}の意味は何ですか？",
                    levels: {
                        N5: [
                            {word: "こんにちは", options: ["早上好", "下午好", "晚上好", "再见"], correct: 1},
                            {word: "ありがとう", options: ["谢谢", "对不起", "请", "再见"], correct: 0},
                            {word: "はい", options: ["是", "不是", "好的", "不好"], correct: 0},
                            {word: "いいえ", options: ["是", "不是", "好的", "不好"], correct: 1},
                            {word: "さようなら", options: ["你好", "谢谢", "再见", "请"], correct: 2}
                        ],
                        N4: [
                            {word: "おはようございます", options: ["下午好", "早上好", "晚上好", "再见"], correct: 1},
                            {word: "すみません", options: ["谢谢", "对不起", "再见", "你好"], correct: 1},
                            {word: "お願いします", options: ["请", "谢谢", "对不起", "再见"], correct: 0},
                            {word: "ただいま", options: ["我回来了", "欢迎回来", "再见", "你好"], correct: 0},
                            {word: "おかえりなさい", options: ["我回来了", "欢迎回来", "再见", "你好"], correct: 1}
                        ],
                        N3: [
                            {word: "挨拶", options: ["打招呼", "道歉", "感谢", "告别"], correct: 0},
                            {word: "初心者", options: ["专家", "初学者", "教师", "学生"], correct: 1},
                            {word: "勉強", options: ["工作", "学习", "休息", "玩耍"], correct: 1},
                            {word: "仕事", options: ["工作", "学习", "休息", "玩耍"], correct: 0},
                            {word: "家族", options: ["朋友", "家人", "同事", "同学"], correct: 1}
                        ],
                        N2: [
                            {word: "効果的", options: ["有效的", "无效的", "有趣的", "无聊的"], correct: 0},
                            {word: "合理的", options: ["合理的", "不合理的", "合适的", "不合适的"], correct: 0},
                            {word: "大幅", options: ["小幅", "大幅", "中等", "微小"], correct: 1},
                            {word: "著しい", options: ["显著的", "微小的", "缓慢的", "快速的"], correct: 0},
                            {word: "効率的", options: ["效率的", "无效的", "有趣的", "无聊的"], correct: 0}
                        ],
                        N1: [
                            {word: "絶妙", options: ["绝妙的", "普通的", "差的", "坏的"], correct: 0},
                            {word: "希薄", options: ["浓厚的", "稀薄的", "强烈的", "微弱的"], correct: 1},
                            {word: "過信", options: ["自信", "过度自信", "相信", "怀疑"], correct: 1},
                            {word: "執着", options: ["执着", "放弃", "坚持", "妥协"], correct: 0},
                            {word: "沈静", options: ["冷静的", "激动的", "安静的", "吵闹的"], correct: 0}
                        ]
                    }
                },
                {
                    pattern: "{word}の読み方は何ですか？",
                    levels: {
                        N5: [
                            {word: "日本", options: ["にほん", "にっぽん", "にぽん", "にほう"], correct: 0},
                            {word: "人", options: ["ひと", "じん", "にん", "ひとり"], correct: 0},
                            {word: "水", options: ["みず", "すい", "みずうみ", "すいどう"], correct: 0},
                            {word: "食べる", options: ["たべる", "たべ", "たべり", "たべます"], correct: 0},
                            {word: "飲む", options: ["のむ", "のみ", "のり", "のみます"], correct: 0}
                        ],
                        N4: [
                            {word: "学校", options: ["がっこう", "がっこ", "がっこうは", "がっこうの"], correct: 0},
                            {word: "仕事", options: ["しごと", "しご", "しごとは", "しごとの"], correct: 0},
                            {word: "勉強", options: ["べんきょう", "べんきょ", "べんきょうは", "べんきょうの"], correct: 0},
                            {word: "家族", options: ["かぞく", "かぞ", "かぞくは", "かぞくの"], correct: 0},
                            {word: "友達", options: ["ともだち", "ともだ", "ともだちは", "ともだちの"], correct: 0}
                        ],
                        N3: [
                            {word: "挨拶", options: ["あいさつ", "あいさ", "あいさつは", "あいさつの"], correct: 0},
                            {word: "初心者", options: ["しょしんしゃ", "しょしん", "しょしんしゃは", "しょしんしゃの"], correct: 0},
                            {word: "効果", options: ["こうか", "こう", "こうかは", "こうかの"], correct: 0},
                            {word: "合理", options: ["ごうり", "ごう", "ごうりは", "ごうりの"], correct: 0},
                            {word: "効率", options: ["こうりつ", "こうり", "こうりつは", "こうりつの"], correct: 0}
                        ],
                        N2: [
                            {word: "効果的", options: ["こうかてき", "こうか", "こうかてきは", "こうかてきの"], correct: 0},
                            {word: "合理的", options: ["ごうりてき", "ごうり", "ごうりてきは", "ごうりてきの"], correct: 0},
                            {word: "大幅", options: ["おおはば", "おお", "おおはばは", "おおはばの"], correct: 0},
                            {word: "著しい", options: ["いちじるしい", "いちじる", "いちじるしいは", "いちじるしいの"], correct: 0},
                            {word: "効率的", options: ["こうりつてき", "こうりつ", "こうりつてきは", "こうりつてきの"], correct: 0}
                        ],
                        N1: [
                            {word: "絶妙", options: ["ぜつみょう", "ぜつ", "ぜつみょうは", "ぜつみょうの"], correct: 0},
                            {word: "希薄", options: ["きはく", "き", "きはくは", "きはくの"], correct: 0},
                            {word: "過信", options: ["かしん", "か", "かしんは", "かしんの"], correct: 0},
                            {word: "執着", options: ["しゅうちゃく", "しゅう", "しゅうちゃくは", "しゅうちゃくの"], correct: 0},
                            {word: "沈静", options: ["ちんせい", "ちん", "ちんせいは", "ちんせいの"], correct: 0}
                        ]
                    }
                }
            ],
            grammar: [
                {
                    pattern: "{sentence}__。",
                    levels: {
                        N5: [
                            {sentence: "私は学生", options: ["です", "ます", "あります", "います"], correct: 0},
                            {sentence: "彼は本を", options: ["読む", "読み", "読みます", "読みました"], correct: 2},
                            {sentence: "昨日、私は映画を", options: ["見る", "見ます", "見ました", "見ません"], correct: 2},
                            {sentence: "明日、私は学校に", options: ["行く", "行きます", "行きました", "行きません"], correct: 1},
                            {sentence: "これは私の", options: ["本", "本で", "本です", "本だ"], correct: 2}
                        ],
                        N4: [
                            {sentence: "私は毎日朝ご飯を", options: ["食べる", "食べます", "食べました", "食べません"], correct: 1},
                            {sentence: "彼は英語が", options: ["話す", "話せる", "話します", "話しました"], correct: 1},
                            {sentence: "私は日本語を", options: ["勉強する", "勉強します", "勉強しました", "勉強しません"], correct: 1},
                            {sentence: "昨日、私は友達と", options: ["遊ぶ", "遊びます", "遊びました", "遊びません"], correct: 2},
                            {sentence: "明日、私は図書館へ", options: ["行く", "行きます", "行きました", "行きません"], correct: 1}
                        ],
                        N3: [
                            {sentence: "私は日本に", options: ["行く", "行きたい", "行きます", "行きました"], correct: 1},
                            {sentence: "彼は毎日勉強して", options: ["いる", "います", "いました", "いません"], correct: 0},
                            {sentence: "私は先生に質問を", options: ["聞く", "聞きます", "聞きました", "聞きません"], correct: 1},
                            {sentence: "昨日、私は雨に", options: ["降る", "降られる", "降ります", "降りました"], correct: 1},
                            {sentence: "明日、私は試験が", options: ["ある", "あります", "ありました", "ありません"], correct: 0}
                        ],
                        N2: [
                            {sentence: "この計画は実現するためには多くの資金と時間が", options: ["必要とされる", "必要である", "必要となる", "必要であった"], correct: 0},
                            {sentence: "彼の言うことはいつも", options: ["当たり前", "当然", "自然", "普通"], correct: 0},
                            {sentence: "彼女はいつも", options: ["速い", "早い", "迅速", "急いで"], correct: 3},
                            {sentence: "この問題は難しすぎて", options: ["解けない", "解けなかった", "解けなくなった", "解けないでいる"], correct: 0},
                            {sentence: "彼は今日も", options: ["一生懸命", "一所懸命", "一所命", "一生命"], correct: 0}
                        ],
                        N1: [
                            {sentence: "彼の提案は非常に", options: ["建設的", "破壊的", "消極的", "積極的"], correct: 0},
                            {sentence: "この現象は科学的に", options: ["説明できる", "説明できない", "説明した", "説明する"], correct: 0},
                            {sentence: "彼女の演技は圧倒的に", options: ["優れている", "劣っている", "普通である", "悪い"], correct: 0},
                            {sentence: "この決定は将来に向かって", options: ["重要な意味を持つ", "重要な意味を持たない", "重要な意味がある", "重要な意味がない"], correct: 0},
                            {sentence: "彼の発言は", options: ["論理的", "非論理的", "合理的", "不合理的"], correct: 0}
                        ]
                    }
                }
            ],
            reading: [
                {
                    pattern: "文章を読んで、質問に答えなさい。\n{passage}\n質問：{question}",
                    levels: {
                        N5: [
                            {passage: "私は毎朝7時に起きます。それから、顔を洗って、朝ご飯を食べます。朝ご飯はパンと牛乳です。その後、学校に行きます。", question: "私の朝ご飯は何ですか？", options: ["パンと牛乳", "ご飯と味噌汁", "うどん", "そば"], correct: 0},
                            {passage: "今日は日曜日です。私は午前中に図書館に行きました。図書館で本を読みました。午後は友達と公園で遊びました。", question: "今日、私は午前中にどこに行きましたか？", options: ["図書館", "公園", "学校", "家"], correct: 0},
                            {passage: "私の家族は四人です。父、母、姉、そして私です。父は会社員です。母は家庭婦人です。姉は大学生です。私は中学生です。", question: "私の家族は何人ですか？", options: ["四人", "三人", "五人", "六人"], correct: 0},
                            {passage: "昨日、私は映画館に行きました。映画はとても面白かったです。映画館の隣にはレストランがあります。そこで晩ご飯を食べました。", question: "昨日、私はどこで晩ご飯を食べましたか？", options: ["レストラン", "映画館", "家", "学校"], correct: 0},
                            {passage: "私の趣味は読書と音楽です。毎週末に図書館に行って本を借ります。また、友達と一緒に音楽を聴きます。", question: "私の趣味は何ですか？", options: ["読書と音楽", "スポーツ", "旅行", "料理"], correct: 0}
                        ],
                        N4: [
                            {passage: "私は毎朝6時半に起きます。それから、散歩に行きます。散歩は30分ぐらいします。その後、朝ご飯を食べて、7時45分に家を出ます。電車で学校に行きます。電車で30分かかります。", question: "私は毎朝何時に家を出ますか？", options: ["7時45分", "6時半", "7時", "8時"], correct: 0},
                            {passage: "昨日はとても忙しかったです。午前中は授業がありました。午後は図書館で勉強しました。夕方からはアルバイトがありました。アルバイトはレストランです。夜9時に終わりました。", question: "昨日、私のアルバイトは何時に終わりましたか？", options: ["夜9時", "午後", "夕方", "午前中"], correct: 0},
                            {passage: "私の家族は父、母、弟の四人です。父は45歳で、会社員です。母は42歳で、教師です。弟は10歳で、小学生です。私は18歳で、大学生です。", question: "私の母は何歳ですか？", options: ["42歳", "45歳", "18歳", "10歳"], correct: 0},
                            {passage: "今日は天気がいいです。午前中に公園に行きました。公園で友達とバスケットボールをしました。午後は家で宿題をしました。晩ご飯は牛肉と野菜の炒め物を作りました。", question: "今日の晩ご飯は何を作りましたか？", options: ["牛肉と野菜の炒め物", "魚", "パスタ", "ラーメン"], correct: 0},
                            {passage: "私の趣味は写真撮影です。毎週末にカメラを持って出かけます。山や海、街など、いろいろな場所を撮ります。去年、写真展に出展する機会がありました。", question: "私の趣味は何ですか？", options: ["写真撮影", "絵を描く", "音楽を聴く", "本を読む"], correct: 0}
                        ],
                        N3: [
                            {passage: "近年、インターネットの普及により、人々のコミュニケーションの方法が大きく変わってきました。メールやSNSを使って、簡単に遠くの人と連絡が取れるようになりました。しかし、その一方で、顔を合わせて話す機会が減ってきたという指摘もあります。", question: "インターネットの普及によってどのような変化が起きましたか？", options: ["遠くの人と簡単に連絡が取れるようになった", "顔を合わせて話す機会が増えた", "コミュニケーションの方法が変わらなかった", "メールが使えなくなった"], correct: 0},
                            {passage: "日本の飲食店では、お客様が入店すると、店員が「いらっしゃいませ」と言います。そして、席に案内して、メニューを渡します。注文が終わると、「少々お待ちください」と言います。食事が終わって会計に行くと、「ありがとうございました」と言います。", question: "日本の飲食店で、お客様が入店すると、店員はどう言いますか？", options: ["いらっしゃいませ", "少々お待ちください", "ありがとうございました", "ごちそうさま"], correct: 0},
                            {passage: "日本の学校では、毎朝の始業式で、校長先生が挨拶をします。そして、生徒たちは校歌を歌います。授業は午前中と午後に分かれています。午前中は4時間、午後は2時間の授業があります。昼休みは12時から1時までです。", question: "日本の学校の昼休みは何時から何時までですか？", options: ["12時から1時まで", "午前中から午後まで", "朝から夜まで", "4時間です"], correct: 0},
                            {passage: "日本の交通ルールでは、車は左側を走ります。信号が赤のときは止まらなければなりません。青のときは進んでもいいです。黄色のときは注意して止まります。また、横断歩道では、歩行者に道を譲らなければなりません。", question: "日本の交通ルールで、信号が赤のときはどうしなければなりませんか？", options: ["止まらなければなりません", "進んでもいいです", "注意して止まります", "走ってもいいです"], correct: 0},
                            {passage: "日本の四季ははっきりしています。春は桜が咲き、暖かくなります。夏は暑くて、雨が多いです。秋は涼しくて、紅葉が美しいです。冬は寒くて、雪が降ります。それぞれの季節に合った行事や食べ物があります。", question: "日本の秋はどのような季節ですか？", options: ["涼しくて、紅葉が美しい", "暑くて、雨が多い", "暖かくて、桜が咲く", "寒くて、雪が降る"], correct: 0}
                        ],
                        N2: [
                            {passage: "現代社会において、情報技術の発展は私たちの生活スタイルを大きく変えています。特にスマートフォンの普及により、いつでもどこでも情報を入手したり、人とコミュニケーションを取ったりすることが可能になりました。しかし、その反面、情報過多に悩む人々も増えています。", question: "スマートフォンの普及によってどのようなことが可能になりましたか？", options: ["いつでもどこでも情報を入手できるようになった", "情報過多に悩む人々が減った", "コミュニケーションが難しくなった", "生活スタイルが変わらなくなった"], correct: 0},
                            {passage: "日本の企業では、近年、働き方改革が叫ばれています。長時間労働が問題視され、労働時間の短縮やフレックスタイムの導入などが進められています。これにより、従業員の仕事と生活のバランスが改善され、生産性の向上も期待されています。", question: "日本の企業で進められている働き方改革にはどのようなものがありますか？", options: ["労働時間の短縮やフレックスタイムの導入", "長時間労働の奨励", "仕事と生活のバランスの悪化", "生産性の低下"], correct: 0},
                            {passage: "健康的な生活を送るためには、適度な運動と栄養バランスの取れた食事が重要です。毎日30分ほどの運動をすることで、体の代謝が活発になり、免疫力も高まります。また、野菜や果物をたくさん食べることで、必要なビタミンやミネラルを摂取することができます。", question: "健康的な生活を送るためには何が重要ですか？", options: ["適度な運動と栄養バランスの取れた食事", "大量の運動と食べ过ぎ", "運動をしないことと偏食", "不健康な食生活"], correct: 0},
                            {passage: "グローバル化の進展により、国際交流が盛んになっています。若者たちは海外へ旅行したり、留学したりする機会が増えています。また、インターネットを通じて、世界中の人々と交流することも可能になりました。これにより、異文化理解が深まり、国際感覚が養われています。", question: "グローバル化の進展によってどのようなことが起きていますか？", options: ["国際交流が盛んになっている", "海外旅行が減っている", "異文化理解が浅くなっている", "国際感覚が失われている"], correct: 0},
                            {passage: "環境問題は現在、世界的な課題となっています。地球温暖化、酸性雨、オゾン層の破壊など、様々な問題が存在します。これらの問題を解決するためには、一人一人の努力が必要です。例えば、節電やリサイクル、環境にやさしい製品の使用などが挙げられます。", question: "環境問題を解決するためには何が必要ですか？", options: ["一人一人の努力", "政府のみの対策", "何もしないこと", "環境に悪い製品の使用"], correct: 0}
                        ],
                        N1: [
                            {passage: "現代社会における情報技術の発展は、私たちの生活に多大な影響を及ぼしています。特に人工知能の進化により、従来は人間の手に頼っていた作業が自動化されつつあります。これにより、生産性の向上が期待される一方で、失業の増加や労働市場の変容など、新たな課題も生じています。", question: "人工知能の進化によってどのような変化が起きていますか？", options: ["従来は人間の手に頼っていた作業が自動化されつつある", "生産性が低下している", "失業が減少している", "労働市場が変わらなくなっている"], correct: 0},
                            {passage: "経済成長と環境保護の両立は、現代社会における重要な課題です。経済成長を追求するあまり、環境破壊が進んでしまった事例も少なくありません。一方で、環境保護を優先しすぎると、経済発展が妨げられる可能性もあります。そのため、両者のバランスを取ることが求められています。", question: "経済成長と環境保護の関係について、正しいのはどれですか？", options: ["両者のバランスを取ることが求められている", "経済成長を優先すべきである", "環境保護を優先すべきである", "どちらも重要ではない"], correct: 0},
                            {passage: "教育の役割は、知識の伝達だけでなく、人格形成や社会的能力の育成にもあります。現代の教育では、記憶力や計算力などの認知能力だけでなく、創造力、批判的思考、協調性などの非認知能力も重視されています。これらの能力は、将来の社会で求められる重要な資質です。", question: "現代の教育で重視されているのはどれですか？", options: ["創造力、批判的思考、協調性などの非認知能力", "記憶力や計算力などの認知能力のみ", "知識の伝達のみ", "何も重視されていない"], correct: 0},
                            {passage: "グローバル化の進展により、異文化間の交流がますます重要になっています。異なる文化背景を持つ人々とのコミュニケーションにおいては、自文化中心主義に陥らず、相手の文化を尊重する姿勢が必要です。また、言語の壁を越えるための努力や、文化的差異を理解するための学習も重要です。", question: "異文化間の交流において必要なことはどれですか？", options: ["相手の文化を尊重する姿勢", "自文化中心主義に陥ること", "言語の壁を無視すること", "文化的差異を無視すること"], correct: 0},
                            {passage: "科学技術の発展は、私たちの生活を便利にする一方で、新たな問題も引き起こしています。例えば、ネットワークの普及により、個人情報の漏洩やサイバー攻撃のリスクが高まっています。また、遺伝子組み換え技術の発展により、倫理的な問題も生じています。これらの問題に対しては、法律や規制の整備が必要です。", question: "科学技術の発展によって引き起こされる問題はどれですか？", options: ["個人情報の漏洩やサイバー攻撃のリスクの高まり", "生活が不便になること", "倫理的な問題が解決されること", "法律や規制が不要になること"], correct: 0}
                        ]
                    }
                }
            ]
        };
    }

    // 根据用户等级生成试题
    generateQuestions(userLevel, totalQuestions = 20) {
        const questions = [];
        const levels = this.getDownwardLevels(userLevel);
        
        // 计算每个等级的题目数量
        const questionsPerLevel = Math.ceil(totalQuestions / levels.length);
        
        // 为每个等级生成题目
        levels.forEach(level => {
            const levelQuestions = this.generateLevelQuestions(level, questionsPerLevel);
            questions.push(...levelQuestions);
        });
        
        // 打乱题目顺序
        this.shuffleArray(questions);
        
        // 截取指定数量的题目
        return questions.slice(0, totalQuestions);
    }

    // 获取向下兼容的等级列表
    getDownwardLevels(userLevel) {
        const allLevels = ['N1', 'N2', 'N3', 'N4', 'N5'];
        const levelIndex = allLevels.indexOf(userLevel);
        if (levelIndex === -1) {
            return ['N5'];
        }
        return allLevels.slice(levelIndex);
    }

    // 为指定等级生成题目
    generateLevelQuestions(level, count) {
        const questions = [];
        const questionTypes = Object.keys(this.questionTemplates);
        
        while (questions.length < count) {
            const type = this.randomElement(questionTypes);
            const templates = this.questionTemplates[type];
            const template = this.randomElement(templates);
            
            if (template.levels[level]) {
                const questionData = this.randomElement(template.levels[level]);
                const question = this.buildQuestion(template.pattern, questionData, type, level);
                questions.push(question);
            }
        }
        
        return questions;
    }

    // 构建题目
    buildQuestion(pattern, data, type, level) {
        let questionText = pattern;
        
        // 替换模板中的变量
        Object.keys(data).forEach(key => {
            if (key !== 'options' && key !== 'correct') {
                questionText = questionText.replace(`{${key}}`, data[key]);
            }
        });
        
        // 生成知识点标签
        const tags = [
            `${level}${type === 'vocabulary' ? '词汇' : type === 'grammar' ? '语法' : '阅读'}`,
            this.getRandomTag(type, level)
        ];
        
        return {
            id: Date.now() + Math.random(),
            question: questionText,
            options: data.options,
            correct: data.correct,
            type: type === 'vocabulary' ? '词汇' : type === 'grammar' ? '语法' : '阅读',
            level: level,
            tags: tags,
            explanation: this.generateExplanation(type, data, level)
        };
    }

    // 生成解析
    generateExplanation(type, data, level) {
        if (type === 'vocabulary') {
            return `本题考察${level}级词汇。${data.word}的意思是${data.options[data.correct]}。`;
        } else if (type === 'grammar') {
            return `本题考察${level}级语法。正确答案是${data.options[data.correct]}，用于表示${this.getGrammarExplanation(data)}。`;
        } else if (type === 'reading') {
            return `本题考察${level}级阅读能力。根据文章内容，正确答案是${data.options[data.correct]}。`;
        }
        return '';
    }

    // 获取语法解析
    getGrammarExplanation(data) {
        const explanations = {
            'です': '判断句，表示"是"',
            'ます': '动词礼貌形，表示"做"',
            'あります': '表示"有"（无生命）',
            'います': '表示"有"（有生命）',
            'た': '过去式',
            'ている': '正在进行',
            'たい': '想要',
            'れる': '被动',
            'せる': '使役',
            'ために': '为了',
            'ように': '为了',
            'から': '因为',
            'ので': '因为',
            'けど': '但是',
            'でも': '但是',
            'たら': '如果',
            'なら': '如果',
            'と': '如果',
            'れば': '如果'
        };
        
        const correctOption = data.options[data.correct];
        for (const [key, explanation] of Object.entries(explanations)) {
            if (correctOption.includes(key)) {
                return explanation;
            }
        }
        
        return '语法用法';
    }

    // 获取随机标签
    getRandomTag(type, level) {
        const tags = {
            vocabulary: ['名词', '动词', '形容词', '副词', '形容动词'],
            grammar: ['句型', '助词', '时态', '敬语', '被动'],
            reading: ['短文', '中长文', '说明文', '议论文', '记叙文']
        };
        
        return this.randomElement(tags[type] || []);
    }

    // 随机选择数组元素
    randomElement(array) {
        return array[Math.floor(Math.random() * array.length)];
    }

    // 打乱数组
    shuffleArray(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }

    // 根据用户历史生成个性化试题
    generatePersonalizedQuestions(userLevel, userHistory = [], totalQuestions = 20) {
        const questions = this.generateQuestions(userLevel, totalQuestions);
        
        // 根据用户历史调整题目难度和类型
        if (userHistory.length > 0) {
            // 分析用户弱点
            const weakAreas = this.analyzeWeakAreas(userHistory);
            
            // 增加弱点领域的题目
            const personalizedQuestions = questions.map(question => {
                if (weakAreas.includes(question.type) && Math.random() > 0.5) {
                    // 生成更适合用户弱点的题目
                    return this.generateLevelQuestions(question.level, 1)[0];
                }
                return question;
            });
            
            return personalizedQuestions;
        }
        
        return questions;
    }

    // 分析用户弱点
    analyzeWeakAreas(userHistory) {
        const wrongAnswers = userHistory.filter(item => !item.correct);
        const typeCounts = {};
        
        wrongAnswers.forEach(item => {
            typeCounts[item.type] = (typeCounts[item.type] || 0) + 1;
        });
        
        // 找出错误率最高的类型
        const sortedTypes = Object.entries(typeCounts)
            .sort((a, b) => b[1] - a[1])
            .map(([type]) => type);
        
        return sortedTypes.slice(0, 2); // 返回前两个弱点
    }
}

// 导出模块
module.exports = AIQuestionGenerator;

// 全局实例
if (typeof window !== 'undefined') {
    window.AIQuestionGenerator = AIQuestionGenerator;
    window.aiQuestionGenerator = new AIQuestionGenerator();
}
