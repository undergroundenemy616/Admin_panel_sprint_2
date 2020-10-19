# README #

Routes:
---------

####FLASK -> Django ####
#####Office
* /office  ->  /offices/ 
* /offices/<office_id> ->
#####Zone
* /zone  ->  /zones/
* /zones/<zone_id>  ->  /zones/
#####Floor
* /floor  ->  /floors/
* /floors/<id>  ->  /floors/<id>/
* /floor_map  ->  /floors/floormaps/
* /floor_map/clean  ->  /floors/floormaps/ *Method: delete*
#####Room  
* /room  ->  /rooms/
* /rooms/<room_id> ->
* /room_map/  ->  /rooms/room_marker/
#####Table
* /table  ->  /tables/
* /tables/<table_id> ->
* /table/activate ->
* /table/recieve ->
* /table_status_recieve ->
* /table_tag  ->  /tables/table_tag/
* /table_tags/<tag_id> ->
* /table/rate  ->  ...
#####Room Type
* /room/type  ->  /room_types/
* /room/type/<type_id> -> /room_types/<id>
##### User and Account actions
* /auth ->
* /register/admin ->
* /refresh ->
* /auth_employee ->
* /register_employee ->
* /register_user ->
* /register_kiosk ->
* /register_kiosk/<account_id> ->
* /auth_kiosk ->
* /account ->
* /accounts_list ->
* /accounts/<account_id> ->
* /account_confirm ->
* /groups ->
* /group/<group_id> ->
* /groups/update ->
* /groups/import_single ->
* /groups/import_list ->
* /groups/import_titles
* /enter
* /service_email
* /pass_change
* /pass_reset
* /operator_promotion
#####Booking
* /book
* /book/mobile
* /book/fast
* /book/fast/mobile
* /book/slots
* /book/end
* /books/<book_id>
* /book/activate
* /book/deactivate
* /book_operator
* /book_operator/fast
* /book_list/table
* /book_list/my
* /book_list/user
* /book_list/active
#####License
* /license ->
* /license/<license_id> ->
#####Files
* /files ->
#####Feedback and Reports
* /feedback ->
* /report ->
* /report/history ->
