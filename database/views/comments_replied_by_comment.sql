CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `comments_replied_by_comment` AS
    SELECT 
        `u`.`id` AS `po_fbid`,
        `u`.`idhash` AS `po_id`,
        `u`.`name` AS `post_owner`,
        `u2`.`id` AS `friend_fbid`,
        `u2`.`idhash` AS `friend_id`,
        `u2`.`name` AS `friend`,
        COUNT(`r`.`id`) AS `total_interactions`
    FROM
        ((((((`user` `u`
        JOIN `profile` `p` ON ((`u`.`idhash` = `p`.`user_idhash`)))
        JOIN `post` `pt` ON ((`p`.`user_idhash` = `pt`.`user_idhash`)))
        JOIN `comment` `r` ON ((`pt`.`id` = `r`.`post_id`)))
        JOIN `user` `u2` ON ((`r`.`user_idhash` = `u2`.`idhash`)))
        JOIN `comment_has_comment` `c2` ON ((`r`.`id` = `c2`.`comment_id`)))
        JOIN `comment` `c3` ON (((`c3`.`id` = `c2`.`comment_id1`)
            AND (`c3`.`user_idhash` = `u`.`idhash`))))
    WHERE
        (`u`.`name` <> `u2`.`name`)
    GROUP BY `u`.`idhash` , `u2`.`idhash` , `u`.`name` , `u2`.`name` , `u`.`id` , `u2`.`id`
    ORDER BY `u`.`name` , COUNT(`r`.`id`) DESC