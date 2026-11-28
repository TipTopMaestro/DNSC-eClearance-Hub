DEFAULT
Method	    Endpoint                                            Authentication	Success
GET         /                                                   None            200
GET         /health                                             None            200

Authentication
Method	    Endpoint                                            Authentication	Success
POST	    /api/v1/auth/login	                                None	        200
GET	        /api/v1/auth/me	                                    Bearer token	200
POST	    /api/v1/auth/logout	                                Bearer token	200

Students
Method	    Endpoint                                            Authentication	Success
GET	        /api/v1/students/me	                                STUDENT	        200
GET	        /api/v1/clearance/me	                            STUDENT	        200

Administration
POST        /api/v1/admin/sync/registrar                        ADMIN           200
GET	        /api/v1/admin/sync/registrar/{sync_id}/rejections	ADMIN	        200
POST	    /api/v1/admin/periods	                            ADMIN	        201
GET	        /api/v1/admin/imports	                            ADMIN	        200
GET	        /api/v1/admin/rejections	                        ADMIN	        200
GET	        /api/v1/admin/audit	                                ADMIN	        200

Clearance Deadlines
Method	    Endpoint                                            Authentication	Success
GET	        /api/v1/deadlines/current	                        Bearer token	200

Staff
Method	    Endpoint                                            Authentication	Success
GET	        /api/v1/staff/students	                            STAFF	        200
GET	        /api/v1/staff/clearance/{student_id}	            STAFF	        200
PATCH	    /api/v1/staff/clearance/{student_id}	            STAFF	        200


Required and optional query parameters
Endpoint	                                        Parameter	        Required	Default
/api/v1/clearance/me	                            period_id	        Yes	        —
/api/v1/staff/clearance/{student_id}	            period_id	        Yes	        —
/api/v1/admin/sync/registrar/{sync_id}/rejections	limit, offset	    No	        100, 0
/api/v1/admin/imports	                            limit, offset	    No	        100, 0
/api/v1/admin/rejections	                        limit, offset	    No	        100, 0
/api/v1/admin/audit	                                limit, offset	    No	        100, 0