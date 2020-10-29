**本ハンズオン概要**

本ハンズオンはVoice of Customer Integration
ソリューションのハンズオンです。

最初にソリューションのコアのサービスである、Amazon Transcribe と Amazon
Comprehend のサービスを AWS SDK for Python boto3 を用いた API
経由で動かした後、AWS CloudFormation でVoice of Customer Integration
ソリューションをデプロイし、データを投入して分析結果の可視化を行います。

---

**全体の流れ**

1.  SageMaker Notebook インスタンスを作成（本ハンズオンの実行環境）

2.  Amazon Transcribe と Amazon Comprehend をboto3 を利用して実行する

3.  Voice of Customer Integration ソリューションをデプロイする

4.  Voice of Customer Integration
    ソリューションにデータを流し込んで利用してみる

---

1.  **SageMaker Notebook インスタンスを作成**

配布されたURLをブラウザ（Chrome/FireFox推奨）で開き、「Accept Terms &
Login」をクリックします。

![](media/image1.png)

「AWS Console」 をクリックします

![](media/image2.png)

「Open AWS Console」 をクリックします。（別タブでAWS
マネジメントコンソールが開かれます）

![](media/image3.png)

「サービスを検索する」のテキストボックスに 「SageMaker」 と打ち込み、
表示された 「Amazon SageMaker」 をクリックします。

![](media/image4.png)

左のペインにある「ノートブックインスタンス」をクリックします。

![](media/image5.png)

「ノートブックインスタンスの作成」をクリックします。

![](media/image6.png)

ノートブックインスタンス名に任意の名前を入力（例：VoC-handson-{yyyymmdd}-{name}など）します。また、IAMロールの部分にある「TeamRole」
と書かれたドロップダウンをクリックし、「新しいロールの作成」をクリックします。

![](media/image7.png)

ラジオボタンが表示されますので、「任意の S3
バケット」をクリックしてロールの作成をクリックします。

![](media/image8.png)

「Git
リポジトリ」をクリックし、「なし」になっているドロップダウンをクリックし、「このノートブックインスタンスのみにパブリック
Git リポジトリのクローンを作成する」をクリックします。

![](media/image9.png)

「Git リポジトリの URL」 というテキストボックスに、

<https://github.com/kazuhitogo/voice-of-customer-integration-handson>

と入力し、「ノートブックインスタンスの作成」をクリックします。

![](media/image10.png)

「ステータス」が「Penging」もしくは「In
Progress」になっていることを確認します。

![](media/image11.png)

ノートブックインスタンスからComprehend、Transcribe、S3の公開権限をつけるため、IAMロールを編集します。サービスからIAMを検索して、**新しいタブ**（またこのSageMakerの画面に戻ります）で開いてください。

![](media/image12.png)

左のペインから「ロール」をクリックしてください。

![](media/image13.png)

先程作成した、「Amazon
Sagemaker-ExecutionRole-YYYYMMDDTHHMMSS」のロールをクリックしてください。

![](media/image14.png)

「ポリシーをアタッチします」をクリックしてください。

![](media/image15.png)

検索テキストボックスに「Transcribe」と入力して、「AmazonTranscribeFullAccess」をチェック、「Comprehend」と入力して、ComprehendFullAccessをチェック、「S3」と入力して「AmazonS3FullAccess」をチェックして、「ポリシーのアタッチ」をクリックします。

![](media/image16.png)

![](media/image17.png)

![](media/image18.png)

Amazon
SageMakerの画面に戻り、「InService」になっていることを確認したら「Jupyter
を開く」をクリックします。

![](media/image19.png)

---

2. **Amazon Transcribe と Amazon Comprehend をboto3
    を利用して実行する**

「part1_use_service_on_cui」をクリックします。

![](media/image20.png)

「Transcribe_and_comprehend.ipynb」をクリックします。

![](media/image21.png)

（以降、ノートブックに記載に従っていください）

---

3. **Voice of Customer Integration ソリューションをデプロイする**

jupyter
のファイル一覧画面に戻り、「voice-ofcustomer-integration-handson」をクリックします。

![](media/image22.png)

「part2_solution」をクリックします。

![](media/image23.png)

「setup.ipynb」をクリックします。

![](media/image24.png)

2番目のセルにグローバルで一意なbucket名を入れます。

例：voice-of-customer-{name}-{yyyymmdd}など

![](media/image25.png)

「Cell」をクリックし、「Run All」をクリックします。

![](media/image26.png)

ファイル一覧画面に戻り、export.ndjsonにチェックを入れて、「Download」をクリックします。（手元のPCにexport.ndjsonがダウンロードされます）

![](media/image27.png)

AWSマネジメントコンソールでSageMakerを開いているタブに戻り、サービスから「S3」検索し、S3をクリックします。

![](media/image28.png)

先程入力したバケット名をクリックします。

例）voice-of-customer-{name}-{yyyymmdd}

![](media/image29.png)

「asset」→「template」→「quickstart-connect-voice-base-pipeline.yaml」の順にクリックします。

![](media/image30.png)

![](media/image31.png)

![](media/image32.png)

オブジェクト URL
をクリップボードにコピーします。（念の為テキストエディタ等にも貼り付けておいてください）

![](media/image33.png)

サービスのテキストボックスで「CloudFo」と入力し、「CloudFormation」をクリックします。

![](media/image34.png)

「スタックの作成」をクリックします。

![](media/image35.png)

Amazon S3 URLのテキストボックスに、先程コピーしたテキストを貼り付けます。

例：https://voice-of-customer-{name}-{yyyymmdd}.s3-ap-northeast-1.amazonaws.com/asset/templates/quickstart-connect-voci-base-pipeline.yaml

「次へ」をクリックします。

![](media/image36.png)

下記設定を入力し、「次へ」をクリックします。

-   スタックの名前：\
    任意の名前（例：voice-of-customer-{name}-{yyyymmdd}）

-   The name of the user that is used to log into kibana.:\
    kibana(デフォルト)

-   Audio transcription S3 Bucket Name:\
    グローバルで一意の名前を入力（例：voice-of-customer-transcription-bucket-{name}-{yyyymmdd}）

-   Quick Start S3 Bucket Name:\
    ノートブックで命名したBucket名（例：voice-of-customer-{name}-{yyyymmdd}）

-   Quick Start S3 Key Prefix:\
    asset/

![](media/image37.png)

下までスクロールして「次へ」をクリックします。

![](media/image38.png)

下までスクロールして、３つのチェックボックス全てにチェックを入れ、「スタックの作成」をクリックします。

![](media/image39.png)

左側のペインがCREATE_COMPLETEになるまで待ちます。

![](media/image40.png)


---

4. **Voice of Customer Integration
    ソリューションにデータを流し込んで利用してみる**

「S3」を検索して「S3」をクリックします。

![](media/image41.png)

CloudFormation のスタックを作成したときに指定した「Audio transcription
S3 Bucket Name」のBucket名をクリックします。

（例：voice-of-customer-transcription-bucket-{name}-{YYYYMMDD}）

![](media/image42.png)

「フォルダを作成」をクリックします。

![](media/image43.png)

テキストボックスに「wav」と入力して保存をクリックします。このフォルダに音声ファイルを入れます。

![](media/image44.png)

「wav」 をクリックします。

![](media/image45.png)

事前に配布した「sample.wav」を画面にドラッグ＆ドロップして「アップロード」をクリックします。（アップロードをトリガに音声ファイルの自動解析が始まります）

![](media/image46.png)

サービスから「CloudFormation」をクリックします。

![](media/image47.png)

先程作成したStack名を選択します。

（例：voice-of-customer-{name}-{yyyymmdd}）

![](media/image48.png)

「出力」をクリックします。

![](media/image49.png)

KibanaPassword欄にあるテキストをコピーし、KibanaUrlのリンクをクリックします。

![](media/image50.png)

Usernameにkibana,Password に先程コピーしたPasswordを入力して「Sign
in」をクリックします。

![](media/image51.png)

新パスワードを入力してSend
をクリックします。新パスワードはセキュリティ要件を満たす必要があります。

![](media/image52.png)

「Explorer on my own」をクリックします。

![](media/image53.png)

左端の下から２番目の「歯車アイコン」をクリックします。（Management）

![](media/image54.png)

「Saved Obejects」をクリックします。

![](media/image55.png)

「Import」をクリックします。

![](media/image56.png)

先程ダウンロードしたexport.ndjsonをドラッグ＆ドロップして、「Import」ボタンをクリックします。

![](media/image57.png)

「Done」をクリックします。

![](media/image58.png)

「Call Dashboard」をクリックします。

![](media/image59.png)

Index Pattern に「call-transcript\*」と入力して、「Next
step」をクリックします。

![](media/image60.png)

Time Filter field nameで LastUpdateTimeを選択し、「Create index
pattern」をクリックします。

![](media/image61.png)

![](media/image62.png)

「ゴミ箱マーク」 をクリックします。

![](media/image63.png)

「Delete」をクリックします。

![](media/image64.png)

左にある上から5つ目のアイコンの「Dashboard」をクリックします。

![](media/image65.png)

ダッシュボードが表示されました！（何も表示されない場合は右上のShow
datesの設定を変更してください。デフォルトの場合は15分前までにアップロードした音声ファイルの結果しか表示されません。）

![](media/image66.png)

データフィルタのインタラクションが設定されておりますのでお試しください。
