"""A small built-in corpus used for distributional word vectors.

The corpus is intentionally broad but tiny: it gives NEBULA enough
co-occurrence signal to place common words in a meaningful 2D map without
downloading anything. Users can paste their own corpus in the UI to sharpen
the map for a domain.
"""

SENTENCES = [
    # nature and landscape
    "the river runs through the green valley toward the sea",
    "a mountain rises above the forest and the cold lake",
    "the glacier melts into a stream of fresh water",
    "clouds gather over the ocean before the storm",
    "the desert is dry and the sun burns the sand",
    "rain falls on the field and the soil drinks the water",
    "the island sits alone in the middle of the ocean",
    "wind moves the trees and carries the seed across the valley",
    "the forest is full of moss and tall pine trees",
    "snow covers the mountain peak in winter",
    "the cave is dark and cold beneath the hill",
    "fire spreads across the dry grass of the plain",

    # animals
    "the dog runs across the yard and barks at the bird",
    "a cat sleeps on the warm floor beside the window",
    "the horse walks slowly along the edge of the field",
    "fish swim in the deep water of the lake",
    "the bird builds a nest in the tree and sings",
    "a wolf hunts alone in the cold forest at night",
    "the bee moves from flower to flower in the garden",
    "the whale sings in the dark ocean",

    # people and feeling
    "she felt happy and calm after the long walk",
    "he was angry and sad about the terrible news",
    "the child laughed with joy at the funny story",
    "they were afraid of the dark and the strange noise",
    "her voice was warm and kind to the tired guests",
    "the crowd cheered with excitement when the team won",
    "he felt lonely and quiet in the empty house",
    "the music was beautiful and made everyone smile",
    "a calm mind helps the body rest and heal",
    "the story was boring and the ending felt weak",

    # thought and language
    "the writer typed a sentence on the page",
    "language is a system of words and meaning",
    "the teacher explained the idea with a simple example",
    "she read the book and thought about the ending",
    "a question needs a clear answer and a good reason",
    "the poem uses rhythm and sound to carry feeling",
    "he spoke in a low voice about the difficult choice",
    "the meaning of the word depends on the context",
    "a good argument needs evidence and logic",
    "the student wrote an essay about history and memory",

    # science and math
    "the scientist measured the temperature of the liquid",
    "an atom is made of a nucleus and electrons",
    "the graph shows a curve that rises and then falls",
    "energy moves from the sun to the plant and the animal",
    "the equation describes the motion of the falling body",
    "light travels faster than sound through the air",
    "the experiment produced a small change in pressure",
    "numbers and symbols form the language of mathematics",
    "the orbit of the planet is a wide ellipse",
    "heat flows from the warm body to the cold body",

    # technology
    "the computer runs a program and stores the data",
    "a network connects the phone to the server",
    "the algorithm sorts the list and finds the answer",
    "software needs a test before the team ships it",
    "the robot moves its arm and picks up the part",
    "a password protects the account from an attack",
    "the database holds the record of every user",
    "the camera captures the image and the sensor reads the light",
    "a model learns from data and predicts the next word",
    "the browser loads the page and draws the chart",

    # work and money
    "the company hired a team to build the product",
    "the market fell after the report about the loss",
    "she started a small business and hired two people",
    "the price of the house rose over the year",
    "a manager leads the group and sets the goal",
    "the bank lent money for the new factory",
    "the job needs skill, time and careful work",
    "they signed the contract and started the project",

    # city and travel
    "the city is loud and bright at night",
    "a train carries people from the town to the city",
    "the road is empty and the car moves fast",
    "they walked through the busy street to the station",
    "the bridge crosses the river near the old market",
    "a plane flies above the cloud toward a distant country",

    # food and body
    "she cooked rice and vegetables for dinner",
    "the bread is warm and the soup tastes sweet",
    "he drank cold water after the long run",
    "the fruit is ripe and full of sugar",
    "the body needs sleep, food and clean water",
    "the doctor checked the heart and the lungs",

    # art and sound
    "the painting shows a dark sky over a bright field",
    "the song has a slow beat and a soft voice",
    "the film tells a sad story about a lost friend",
    "the dancer moves across the stage with grace",
    "a photograph holds a moment of light and color",

    # time and change
    "the season changes and the days grow short",
    "the old building was torn down last year",
    "history repeats the same pattern of rise and fall",
    "the future is open and full of unknown choice",
    "a small change in the system can grow over time",
    "the memory of that day slowly fades",

    # abstract relations
    "the cause of the problem was a simple error",
    "a strong community shares trust and common purpose",
    "the rule applies to every case without exception",
    "a good design is simple, clear and useful",
    "the plan failed because the team lacked time",
    "truth and doubt sit close together in the mind",
]
