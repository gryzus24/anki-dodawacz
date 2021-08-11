gryzus_std_front = '''<div id="questionSide">
  <div id="questionBox">
    <div id="definition">{{Definicja}}</div>
    <div id="syn">{{Synonimy}}</div>
    <div id="psyn">{{Przykłady}}</div>
    <div>{{type:Słowo}}</div>
  </div>

  <div id="answerBox">
    <div id="zdanie">{{Przykładowe zdanie}}</div>
    <div id="pos">{{Części mowy}}</div>
    <div id="etym">{{Etymologia}}</div>
  </div>
</div>'''

gryzus_std_back = '''<div id="answerSide">
  {{FrontSide}}
  {{Audio}}
</div>'''

gryzus_std_css = '''.card {
  font-family:;
  font-size: 30px;
  text-align: center;
  background-color: #FBFBEF; #F1F9F6;
  margin-left: 12%;
  margin-right: 12%;
  margin-top: 10px;
}
.mobile .card {
  font-size: 22px;
}
.night_mode.card {
  background-color: #060606;
}

#questionBox {
  margin-top: 1em;
}
@media screen and (max-width: 900px) {
  #questionBox {
    margin-left: -10%;
    margin-right: -10%;
    margin-top: 0px;
  }
}

#answerBox {
  margin-top: 2em;
}
@media screen and (max-width: 900px) {
  #answerBox { 
    margin-left: -10%;
    margin-right: -10%;
    margin-top: 1em;
  }
}

/* Hide answerBox on question side. */
:not(#answerSide) > #questionSide rt,
:not(#answerSide) > #questionSide #answerBox {
   visibility: hidden;
}

#definition {
  color: black;
  margin-bottom: 0.7em;
}
.night_mode #definition {
  color: #EEE;
}

#syn {
  font-size: 0.85em;
  color: #DA8547;
  margin-bottom: 0em;
}
.night_mode #syn {
  color: #DA8547;
}

#psyn {
  font-size: 0.85em;
  margin-top: 0.25em; 
  color: #777;
  margin-bottom: 4em;
}
.night_mode #psyn {
  color: #c0c0c0;
}

#zdanie {
  font-size: 1.15em;
  margin-bottom: 1.5em;
  color: #495F75;
}
.night_mode #zdanie {
  color: #99a;
}

#pos  {
  font-size: 0.8em; 
  color: #DA8547;
  margin-top: 1em;
}
.night_mode #pos {
  color: #cca;
}

#etym {
  font-size: 0.7em;
  margin-top: 0.5em; 
  color: grey;
  margin-bottom: 1em;
}
.night_mode #etym {
  color: #777;
}

input {
  font-size: 38px !important;
  width: 80% !important;
  color: black;
  background-color: #F1F9F6 !important;
  border-radius: 6px;
  border-style: groove;
  padding-left: 0.3em;
}
.night_mode input {
  color: white;
  background-color: #060606 !important;
  border-style: solid;
  border-color: grey;
  border-width: thin;
}

.typeGood {
  background: #13C700;
  font-size: 38px;
  color: black;
  border-radius: 0px;
  padding-right: 3px;
  padding-left: 3px;
}
.mobile .typeGood {
  font-size: 30px;
}
.night_mode .typeGood {
  background: green;
}

.typeBad {
  background: red;
  font-size: 38px;
  color: black;
  border-radius: 0px;
  padding-right: 3px;
  padding-left: 3px;
}
.mobile .typeBad {
  font-size: 30px;
}

.typeMissed {
  background: orange;
  color: black;
  font-size: 38px;
  border-radius: 0px;
  padding-right: 3px;
  padding-left: 3px;
}
.mobile .typeMissed {
  font-size: 30px;
}

.replay-button svg circle {
  fill: white;
}
.replay-button svg path {
  stroke: white;
  fill: grey;
}
.night_mode .replay-button svg circle {
  fill: #777;
}
.night_mode .replay-button svg path {
  stroke: #060606;
  fill: #060606;
}'''

available_notes = {
    'gryzus-std': {
        'modelName': 'gryzus-std',
        'cardName': 'Definition-vocab card',
        'css': gryzus_std_css,
        'front': gryzus_std_front,
        'back': gryzus_std_back,
        'fields': [
            'Definicja',
            'Synonimy',
            'Przykłady',
            'Słowo',
            'Przykładowe zdanie',
            'Części mowy',
            'Etymologia',
            'Audio'
        ]
    }
}
