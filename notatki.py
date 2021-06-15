gryzus_card_front = '''<div id="questionSide">
  <div id="contentContainer">
    <div id="questionBox">
      <div id="definition">{{Definicja}}</div>
      <div id="etym">{{Disambiguation}}</div>
      <div>{{type:Słowo}}</div>
    </div>

    <div id="answerBox">
      <div id="zdanie">{{Przykładowe zdanie}}</div>
      <div id="PoS">{{Części mowy}}</div>
      <div id="etym">{{Etymologia}}</div>
    </div>
  </div>
</div>'''

gryzus_card_back = '''<div id="answerSide">
  {{FrontSide}}
  <div id="etym">{{Audio}}</div>
</div>'''

gryzus_card_css = '''html { height: 100%; }
.card {
  #Height: 100%;
  display: -webkit-box;
  -webkit-box-align: stretch;
  -webkit-box-pack: center;
  -webkit-box-orient: vertical;
  margin: 0;
  padding: 0;
  font-family;
  text-align: center;
  background-color: #060606;
}
.card.night_mode {
  background-color: #060606;
}

#questionBox {
  font-size: 24px;
  margin-left: 12%;
  margin-right: 12%;
  margin-top: 1.5em;
  margin-bottom: 2em;
}

/* Hide answerBox on question side. */
:not(#answerSide) > #questionSide rt,
:not(#answerSide) > #questionSide #answerBox {
   visibility: hidden;
}

#answerBox { 
  padding: 5px;
  margin-left: 10%;
  margin-right: 10%;
  border-radius: 1.2em;
  background-color: 0;
}
.night_mode #answerBox {
  background-color: 0;
}

#definition {
  color: #FFFFFF;
  margin-bottom: 0.7em;
}
.night_mode #definition {
  color: #FFFFFF;
}

#stopgap {
  font-size: 1em;
  color: #ADD8E6
}
.night_mode #stopgap {
  color: #ADD8E6;
}

#PoS  {
  font-size: 1.6em; 
  color: #cca;
  margin-top: 1em;
}
.night_mode #PoS {
  color: #cca;
}

.typeGood {
background: green;
font-size: 34px;
color: black;
border-radius: 0px;
padding-right: 3px;
padding-left: 3px;
margin: 0rem;
}

.typeBad {
background: red;
font-size:34px;
color: black;
border-radius: 0px;
padding-right: 3px;
padding-left: 3px;
margin: 0rem;
}

.typeMissed {
background: orange;
color: black;
font-size: 34px;
border-radius: 0px;
padding-right: 3px;
padding-left: 3px;
margin: 0rem;
}

input {
font-size: 30px !important;
font-family;
width: 75% !important;
color: white;
background-color: #060606 !important;
border-style: hidden;
margin: 0em;
padding-left: 0.3em;
text-align: left;
}

#zdanie {
  font-size: 34px;
  margin-top: 0em; 
  color: #99a;
}
.night_mode #zdanie {
  color: #99a;
}

#etym {
  font-size: 1em;
  margin-top: 0.5em; 
  color: #777;
  width: 100%;
  height: 100%;
  margin: 7px auto 20px;
  margin-bottom: 3em;
}
.night_mode #etym {
  color: #777;
}'''

available_notes = {
    'gryzus-dark': {
        'name': 'gryzus-dark',
        'css': gryzus_card_css,
        'front': gryzus_card_front,
        'back': gryzus_card_back,
        'fields': [
            'Definicja',
            'Disambiguation',
            'Słowo',
            'Przykładowe zdanie',
            'Części mowy',
            'Etymologia',
            'Audio'
        ]
    }
}
