# Python-Socket-Programming
Text based adventure made with python socket programming.

## Sample Commands for 4 rooms, 3 players
python3 discovery.py
python3 room.py "study" "There are lot's of books... There is a kitchen to the east and a living room to the south." "book" "scotch" "globe" -e "kitchen" -s "living" .
python3 room.py "kitchen" "A kitchen, there is a study to the west, and an opening to a backyard to the south" "bannana" "apple" "knife" -w "study" -s "backyard" .
python3 room.py "living" "Living room there is 2 couches and a large glass window. There is a study to the north, and a backyard to the east" "letter" "pen" "pillow" -n "study" -e "backyard" .
python3 room.py "backyard" "Lot's of open green space, looks like it's fenced off. There is a living room to the west and a kitchen to the north" "ball" "gnome" "bones" -n "kitchen" -w "living" .
python3 player.py user1 study
python3 player.py user2 study
python3 player.py user3 study
