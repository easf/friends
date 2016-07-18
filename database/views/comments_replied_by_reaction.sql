CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `comments_replied_by_reaction` AS
    SELECT 
        `u`.`id` AS `po_fbid`,
        `u`.`idhash` AS `po_id`,
        `u`.`name` AS `post_owner`,
        `u2`.`id` AS `friend_fbid`,
        `u2`.`idhash` AS `friend_id`,
        `u2`.`name` AS `friend`,
        COUNT(`r`.`id`) AS `total_interactions`
    FROM
        (((((`user` `u`
        JOIN `profile` `p` ON ((`u`.`idhash` = `p`.`user_idhash`)))
        JOIN `post` `pt` ON ((`p`.`user_idhash` = `pt`.`user_idhash`)))
        JOIN `comment` `r` ON ((`pt`.`id` = `r`.`post_id`)))
        JOIN `user` `u2` ON ((`r`.`user_idhash` = `u2`.`idhash`)))
        JOIN `reaction` `r2` ON ((`r`.`id` = `r2`.`comment_id`)))
    WHERE
        ((`u`.`name` <> `u2`.`name`)
            AND (`r2`.`user_idhash` = `u`.`idhash`))
    GROUP BY `u`.`idhash` , `u2`.`idhash` , `u`.`name` , `u2`.`name` , `u`.`id` , `u2`.`id`
    ORDER BY `u`.`name` , COUNT(`r`.`id`) DESC